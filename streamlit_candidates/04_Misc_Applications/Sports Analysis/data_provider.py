import streamlit as st

"""
data_provider.py - The Odds API 資料提供者

封裝所有與 The Odds API 的互動邏輯，包含：
- 速率限制管理（月額度追蹤 + 動態每日上限計算）
- 指數退避重試（針對 429 / 5xx）
- 資料標準化為 OddsRecord dataclass

【設計決策】
- 使用同步 `requests` 而非 `aiohttp`。
- 在 main.py 中透過 asyncio.loop.run_in_executor() 將阻塞式 I/O 包裝為非同步，
  避免事件迴圈被佔用。此方式比 aiohttp 更易於測試與除錯，且 The Odds API
  的請求頻率本身有限制，並發需求不高。
"""

import json
import logging
import math
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Any, Optional

import requests

from config import ApiConfig

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 標準化資料結構
# ---------------------------------------------------------------------------

@dataclass
class OddsRecord:
    """
    單筆賠率快照的標準化資料結構。

    所有下游模組（OddsDatabase、ArbitrageAnalyzer）均以此結構為輸入/輸出介面，
    確保模組間的解耦與資料一致性。
    """
    match_id: str           # The Odds API 賽事唯一識別碼
    sport: str              # 運動類型（e.g., "basketball_nba"）
    home_team: str          # 主場隊伍名稱
    away_team: str          # 客場隊伍名稱
    platform: str           # 博彩平台（bookmaker）識別碼
    odds_home: float        # 主場勝出賠率
    odds_away: float        # 客場勝出賠率
    timestamp: datetime     # 抓取時間（UTC）
    latency_ms: float       # API 回應延遲（毫秒）
    commence_time: Optional[datetime] = None   # 賽事開始時間
    odds_draw: Optional[float] = None          # 平局賠率（足球適用）
    raw_json: Optional[str] = None             # 原始 JSON（保留完整稽核軌跡）
    is_valid: int = 1       # 資料有效性（1=有效，0=異常）

    def to_dict(self) -> dict[str, Any]:
        """轉換為字典格式，方便序列化。"""
        d = asdict(self)
        # 將 datetime 轉為 ISO 8601 字串
        if isinstance(d.get("timestamp"), datetime):
            d["timestamp"] = d["timestamp"].isoformat()
        if isinstance(d.get("commence_time"), datetime):
            d["commence_time"] = d["commence_time"].isoformat()
        return d


# ---------------------------------------------------------------------------
# 速率限制計數器
# ---------------------------------------------------------------------------

@dataclass
class RateLimitState:
    """
    追蹤 API 呼叫次數狀態的可變狀態容器。

    設計為獨立類別，方便在測試中替換（Mock）及持久化至本地 JSON 檔案，
    避免程式重啟後計數器歸零。
    """
    monthly_quota: int          # 月額度上限
    calls_this_month: int = 0   # 本月已用次數
    month_key: str = ""         # 格式 "YYYY-MM"，用於偵測月份切換
    state_file: Optional[str] = None  # 持久化 JSON 路徑

    def __post_init__(self) -> None:
        now = datetime.utcnow()
        self.month_key = now.strftime("%Y-%m")
        if self.state_file:
            self._load_from_disk()

    def _load_from_disk(self) -> None:
        """從本地 JSON 讀取上次存儲的計數器狀態。"""
        path = Path(self.state_file)
        if not path.exists():
            return
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if data.get("month_key") == self.month_key:
                self.calls_this_month = data.get("calls_this_month", 0)
                logger.info(
                    "載入速率限制狀態：本月已用 %d 次（月份：%s）",
                    self.calls_this_month, self.month_key
                )
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("讀取速率限制狀態檔案失敗：%s", exc)

    def save_to_disk(self) -> None:
        """將目前計數器狀態持久化至 JSON 檔案。"""
        if not self.state_file:
            return
        path = Path(self.state_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "month_key": self.month_key,
            "calls_this_month": self.calls_this_month,
            "updated_at": datetime.utcnow().isoformat()
        }
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def increment(self) -> None:
        """呼叫一次 API 後增加計數，並檢查是否需要重置月份計數器。"""
        now = datetime.utcnow()
        current_month = now.strftime("%Y-%m")
        if current_month != self.month_key:
            logger.info(
                "偵測到月份切換（%s → %s），重置計數器", self.month_key, current_month
            )
            self.calls_this_month = 0
            self.month_key = current_month
        self.calls_this_month += 1
        self.save_to_disk()

    def remaining_quota(self) -> int:
        """計算本月剩餘額度。"""
        return max(0, self.monthly_quota - self.calls_this_month)

    def usage_ratio(self) -> float:
        """計算本月已用比例（0.0–1.0）。"""
        return self.calls_this_month / max(1, self.monthly_quota)

    def daily_budget(self) -> int:
        """
        動態計算今日建議呼叫上限。

        策略：剩餘額度 / 本月剩餘天數，確保不會在月初就耗盡額度。
        """
        now = datetime.utcnow()
        # 計算到月底（含今天）的剩餘天數
        end_of_month = date(now.year, now.month, 1) + timedelta(days=32)
        end_of_month = end_of_month.replace(day=1) - timedelta(days=1)
        days_left = max(1, (end_of_month - now.date()).days + 1)
        budget = math.ceil(self.remaining_quota() / days_left)
        return budget


# ---------------------------------------------------------------------------
# API 客戶端
# ---------------------------------------------------------------------------

class OddsApiClient:
    """
    The Odds API 同步客戶端。

    負責：
    1. 發送 HTTP 請求並取得賠率數據
    2. 速率限制管理（月額度 + 每日預算 + 安全緩衝）
    3. 指數退避重試（429 / 5xx）
    4. 回應資料正規化為 OddsRecord 列表
    """

    def __init__(self, config: ApiConfig, state_file: Optional[str] = None) -> None:
        """
        初始化 API 客戶端。

        Args:
            config: ApiConfig 設定物件
            state_file: 速率限制狀態持久化路徑（可選）
        """
        self._config = config
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": config.user_agent,
            "Accept": "application/json"
        })
        self._rate_state = RateLimitState(
            monthly_quota=config.monthly_quota,
            state_file=state_file or "./data/rate_limit_state.json"
        )
        self._last_call_ts: float = 0.0
        logger.info(
            "OddsApiClient 初始化完成。本月已用：%d/%d 次。今日建議上限：%d 次。",
            self._rate_state.calls_this_month,
            self._rate_state.monthly_quota,
            self._rate_state.daily_budget()
        )

    # ------------------------------------------------------------------
    # 速率限制內部方法
    # ------------------------------------------------------------------

    def _check_quota(self) -> bool:
        """
        檢查是否可安全地發出請求。

        若使用比例超過安全門檻（1 - buffer），記錄警告。
        若額度已完全耗盡，返回 False 以阻止請求。

        Returns:
            True：可繼續請求；False：額度耗盡，應暫停
        """
        usage = self._rate_state.usage_ratio()
        buffer = self._config.quota_safety_buffer
        remaining = self._rate_state.remaining_quota()

        if remaining <= 0:
            logger.error(
                "月額度已耗盡（%d/%d 次）！本月剩餘請求已被阻止。",
                self._rate_state.calls_this_month,
                self._rate_state.monthly_quota
            )
            return False

        if usage >= (1.0 - buffer):
            logger.warning(
                "⚠️  API 用量達到安全門檻（%.1f%%）。剩餘 %d 次、今日建議上限 %d 次。",
                usage * 100, remaining, self._rate_state.daily_budget()
            )

        return True

    def _enforce_rate_limit(self) -> None:
        """強制執行最小請求間隔，避免過於頻繁地呼叫 API。"""
        elapsed = time.monotonic() - self._last_call_ts
        wait_time = self._config.request_interval_seconds - elapsed
        if wait_time > 0:
            logger.debug("速率限制等待 %.2f 秒...", wait_time)
            time.sleep(wait_time)

    def _make_request_with_retry(
        self,
        endpoint: str,
        params: dict[str, Any]
    ) -> dict[str, Any] | list[Any]:
        """
        發送 HTTP GET 請求，實作指數退避重試策略。

        重試策略：
        - 觸發條件：HTTP 429（Too Many Requests）或 5xx（伺服器錯誤）
        - 等待時間：base * 2^attempt 秒（e.g., 2s, 4s, 8s, 16s）
        - 最大重試次數：config.max_retry_attempts

        Args:
            endpoint: API 端點路徑（相對於 base_url）
            params: 請求查詢參數

        Returns:
            解析後的 JSON 資料（dict 或 list）

        Raises:
            requests.HTTPError: 超過重試次數後仍失敗
            RuntimeError: 月額度耗盡
        """
        if not self._check_quota():
            raise RuntimeError("月 API 額度已耗盡，請求被阻止。")

        self._enforce_rate_limit()

        url = f"{self._config.base_url}/{endpoint.lstrip('/')}"
        params = {**params, "apiKey": self._config.api_key}

        for attempt in range(self._config.max_retry_attempts + 1):
            try:
                start_ts = time.monotonic()
                response = self._session.get(
                    url,
                    params=params,
                    timeout=self._config.request_timeout_seconds
                )
                latency_ms = (time.monotonic() - start_ts) * 1000
                self._last_call_ts = time.monotonic()

                # 記錄 API 剩餘額度（從 response header 讀取）
                remaining_from_header = response.headers.get("x-requests-remaining")
                used_from_header = response.headers.get("x-requests-used")
                if remaining_from_header:
                    logger.info(
                        "API 回應 | 延遲：%.0f ms | 剩餘額度（Header）：%s | "
                        "已用額度（Header）：%s",
                        latency_ms, remaining_from_header, used_from_header
                    )

                # 觸發重試的狀態碼
                if response.status_code == 429:
                    wait = self._config.retry_backoff_base ** attempt
                    logger.warning(
                        "收到 429 Too Many Requests。第 %d/%d 次重試，等待 %.1f 秒...",
                        attempt + 1, self._config.max_retry_attempts, wait
                    )
                    time.sleep(wait)
                    continue

                if response.status_code >= 500:
                    wait = self._config.retry_backoff_base ** attempt
                    logger.warning(
                        "收到 %d 伺服器錯誤。第 %d/%d 次重試，等待 %.1f 秒...",
                        response.status_code, attempt + 1,
                        self._config.max_retry_attempts, wait
                    )
                    time.sleep(wait)
                    continue

                response.raise_for_status()
                self._rate_state.increment()
                return response.json(), latency_ms

            except requests.exceptions.ConnectionError as exc:
                wait = self._config.retry_backoff_base ** attempt
                logger.error(
                    "網路連線錯誤（第 %d/%d 次）：%s。等待 %.1f 秒重試...",
                    attempt + 1, self._config.max_retry_attempts, exc, wait
                )
                time.sleep(wait)

        raise requests.HTTPError(
            f"請求 {url} 在 {self._config.max_retry_attempts} 次重試後仍失敗。"
        )

    # ------------------------------------------------------------------
    # 公開 API 方法
    # ------------------------------------------------------------------

    def get_sports(self) -> list[dict[str, Any]]:
        """
        取得所有可用運動項目列表。

        Returns:
            運動項目 dict 列表（含 key、title、has_outrights 等欄位）
        """
        logger.info("正在取得可用運動項目列表...")
        data, _ = self._make_request_with_retry("sports", {"all": "false"})
        logger.info("取得 %d 個運動項目。", len(data))
        return data

    def get_odds(
        self,
        sport_key: str,
        regions: str = "us,uk,eu,au",
        markets: str = "h2h",
        odds_format: str = "decimal"
    ) -> list[OddsRecord]:
        """
        取得指定運動項目的跨平台賠率，並正規化為 OddsRecord 列表。

        Args:
            sport_key: 運動項目識別碼（e.g., "basketball_nba"）
            regions:   博彩平台地區（逗號分隔：us, uk, eu, au）
            markets:   賠率市場類型（h2h=勝負盤, spreads=讓分, totals=大小）
            odds_format: 賠率格式（decimal=歐洲式, american=美式）

        Returns:
            OddsRecord 列表（每個 bookmaker × 賽事 = 一筆記錄）
        """
        logger.info(
            "正在取得 %s 賠率（地區：%s，市場：%s）...",
            sport_key, regions, markets
        )
        params = {
            "sport": sport_key,
            "regions": regions,
            "markets": markets,
            "oddsFormat": odds_format,
            "dateFormat": "iso"
        }
        raw_data, latency_ms = self._make_request_with_retry(
            f"sports/{sport_key}/odds", params
        )
        records = self._normalize_odds(raw_data, sport_key, latency_ms)
        logger.info(
            "已正規化 %d 筆 OddsRecord（來源：%d 場賽事）。",
            len(records), len(raw_data)
        )
        return records

    def get_remaining_quota(self) -> dict[str, Any]:
        """
        回傳目前速率限制狀態摘要（不發出實際 API 請求）。

        Returns:
            包含 calls_this_month、remaining_quota、daily_budget 等資訊的 dict
        """
        return {
            "monthly_quota": self._rate_state.monthly_quota,
            "calls_this_month": self._rate_state.calls_this_month,
            "remaining_quota": self._rate_state.remaining_quota(),
            "usage_ratio_pct": round(self._rate_state.usage_ratio() * 100, 2),
            "daily_budget": self._rate_state.daily_budget(),
            "month_key": self._rate_state.month_key
        }

    # ------------------------------------------------------------------
    # 資料正規化（私有）
    # ------------------------------------------------------------------

    def _normalize_odds(
        self,
        raw_events: list[dict[str, Any]],
        sport_key: str,
        latency_ms: float
    ) -> list[OddsRecord]:
        """
        將 The Odds API 的原始 JSON 回應轉換為 OddsRecord 列表。

        每個 bookmaker × 賽事組合產生一筆 OddsRecord，
        確保下游模組不需了解 API 回應結構。

        Args:
            raw_events: API 回傳的賽事列表
            sport_key:  運動項目識別碼
            latency_ms: 本次請求延遲（毫秒）

        Returns:
            OddsRecord 列表
        """
        records: list[OddsRecord] = []
        fetch_time = datetime.utcnow()

        for event in raw_events:
            match_id = event.get("id", "")
            home_team = event.get("home_team", "")
            away_team = event.get("away_team", "")
            commence_time_raw = event.get("commence_time")
            commence_time: Optional[datetime] = None
            if commence_time_raw:
                try:
                    commence_time = datetime.fromisoformat(
                        commence_time_raw.replace("Z", "+00:00")
                    )
                except ValueError:
                    pass

            bookmakers = event.get("bookmakers", [])
            for bookmaker in bookmakers:
                platform = bookmaker.get("key", "")
                markets = bookmaker.get("markets", [])

                for market in markets:
                    if market.get("key") != "h2h":
                        continue

                    outcomes = {
                        o["name"]: o["price"]
                        for o in market.get("outcomes", [])
                        if "name" in o and "price" in o
                    }

                    odds_home = outcomes.get(home_team)
                    odds_away = outcomes.get(away_team)
                    odds_draw = outcomes.get("Draw")

                    if odds_home is None or odds_away is None:
                        logger.debug(
                            "賽事 %s / 平台 %s 缺少主/客場賠率，跳過。",
                            match_id, platform
                        )
                        continue

                    record = OddsRecord(
                        match_id=match_id,
                        sport=sport_key,
                        home_team=home_team,
                        away_team=away_team,
                        platform=platform,
                        odds_home=float(odds_home),
                        odds_away=float(odds_away),
                        odds_draw=float(odds_draw) if odds_draw else None,
                        timestamp=fetch_time,
                        latency_ms=round(latency_ms, 2),
                        commence_time=commence_time,
                        raw_json=json.dumps(event, ensure_ascii=False),
                        is_valid=1
                    )
                    records.append(record)

        return records
