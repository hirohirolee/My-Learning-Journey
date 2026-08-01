import streamlit as st

"""
tests/test_data_provider.py - OddsApiClient 速率限制與資料正規化測試

涵蓋：
- RateLimitState 月份計算與計數邏輯
- _check_quota() 安全門檻警告
- _normalize_odds() 資料格式轉換
- 指數退避重試邏輯（透過 Mock）
"""

import json
import os
import sys
import tempfile
from datetime import datetime
from unittest.mock import MagicMock, patch, PropertyMock

import pytest
import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from data_provider import OddsApiClient, OddsRecord, RateLimitState
from config import ApiConfig


# ---------------------------------------------------------------------------
# RateLimitState 測試
# ---------------------------------------------------------------------------

class TestRateLimitState:
    """針對速率限制狀態計算的單元測試。"""

    def test_initial_state(self) -> None:
        """初始狀態應為 0 次已用，額度全滿。"""
        state = RateLimitState(monthly_quota=500)
        assert state.calls_this_month == 0
        assert state.remaining_quota() == 500
        assert state.usage_ratio() == 0.0

    def test_increment_increases_count(self) -> None:
        """increment() 應增加計數並減少剩餘額度。"""
        state = RateLimitState(monthly_quota=500)
        state.increment()
        state.increment()
        assert state.calls_this_month == 2
        assert state.remaining_quota() == 498

    def test_remaining_quota_floor_at_zero(self) -> None:
        """已用次數超過額度時，remaining_quota() 應回傳 0 而非負數。"""
        state = RateLimitState(monthly_quota=10)
        for _ in range(15):
            state.calls_this_month += 1
        assert state.remaining_quota() == 0

    def test_usage_ratio_at_full(self) -> None:
        """全額度使用時，usage_ratio() 應為 1.0。"""
        state = RateLimitState(monthly_quota=100)
        state.calls_this_month = 100
        assert state.usage_ratio() == pytest.approx(1.0)

    def test_daily_budget_decreases_with_usage(self) -> None:
        """使用越多，每日建議上限應越低。"""
        state = RateLimitState(monthly_quota=500)
        budget_full = state.daily_budget()

        state.calls_this_month = 400
        budget_low = state.daily_budget()

        assert budget_low < budget_full

    def test_daily_budget_always_positive(self) -> None:
        """即使額度將盡，每日預算至少為 0。"""
        state = RateLimitState(monthly_quota=500)
        state.calls_this_month = 499
        assert state.daily_budget() >= 0

    def test_state_persistence_to_disk(self, tmp_path) -> None:
        """狀態應能正確序列化至 JSON 並重新載入。"""
        state_file = str(tmp_path / "state.json")
        state = RateLimitState(monthly_quota=500, state_file=state_file)
        state.calls_this_month = 42
        state.save_to_disk()

        # 重新載入
        new_state = RateLimitState(monthly_quota=500, state_file=state_file)
        assert new_state.calls_this_month == 42


# ---------------------------------------------------------------------------
# OddsApiClient 初始化測試
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_config() -> ApiConfig:
    """建立不含真實金鑰的測試用 ApiConfig。"""
    return ApiConfig.__new__(ApiConfig)


@pytest.fixture
def test_api_config() -> ApiConfig:
    """直接建立測試用 ApiConfig（繞過環境變數驗證）。"""
    config = object.__new__(ApiConfig)
    object.__setattr__(config, "api_key", "test_fake_key_12345")
    object.__setattr__(config, "base_url", "https://api.the-odds-api.com/v4")
    object.__setattr__(config, "monthly_quota", 100)
    object.__setattr__(config, "quota_safety_buffer", 0.1)
    object.__setattr__(config, "request_interval_seconds", 0.0)  # 測試不等待
    object.__setattr__(config, "max_retry_attempts", 2)
    object.__setattr__(config, "retry_backoff_base", 0.1)  # 測試快速重試
    object.__setattr__(config, "request_timeout_seconds", 10)
    object.__setattr__(config, "user_agent", "TestAgent/1.0")
    return config


@pytest.fixture
def client(test_api_config, tmp_path) -> OddsApiClient:
    """建立使用測試設定的 OddsApiClient。"""
    state_file = str(tmp_path / "rate_state.json")
    return OddsApiClient(config=test_api_config, state_file=state_file)


# ---------------------------------------------------------------------------
# 速率限制邏輯測試
# ---------------------------------------------------------------------------

class TestQuotaManagement:
    """針對速率限制管理的測試。"""

    def test_quota_exhausted_blocks_request(self, client: OddsApiClient) -> None:
        """額度耗盡時，_check_quota() 應回傳 False。"""
        client._rate_state.calls_this_month = client._rate_state.monthly_quota
        assert client._check_quota() is False

    def test_quota_available_allows_request(self, client: OddsApiClient) -> None:
        """有剩餘額度時，_check_quota() 應回傳 True。"""
        client._rate_state.calls_this_month = 0
        assert client._check_quota() is True

    def test_quota_warning_near_limit(self, client: OddsApiClient, caplog) -> None:
        """使用率接近門檻時應記錄警告。"""
        import logging
        # 設定使用率超過安全門檻（90% + 1）
        client._rate_state.calls_this_month = 91
        with caplog.at_level(logging.WARNING):
            client._check_quota()
        assert any("門檻" in record.message for record in caplog.records) or \
               any("%" in record.message for record in caplog.records)

    def test_request_blocked_when_quota_exhausted(
        self, client: OddsApiClient
    ) -> None:
        """額度耗盡時發出請求應拋出 RuntimeError。"""
        client._rate_state.calls_this_month = client._rate_state.monthly_quota
        with pytest.raises(RuntimeError, match="額度"):
            client._make_request_with_retry("sports", {})

    def test_get_remaining_quota_no_api_call(self, client: OddsApiClient) -> None:
        """get_remaining_quota() 不應消耗 API 次數。"""
        initial_count = client._rate_state.calls_this_month
        quota = client.get_remaining_quota()
        assert client._rate_state.calls_this_month == initial_count
        assert "remaining_quota" in quota
        assert "daily_budget" in quota


# ---------------------------------------------------------------------------
# 指數退避重試測試
# ---------------------------------------------------------------------------

class TestRetryLogic:
    """針對指數退避重試邏輯的測試（使用 Mock）。"""

    def test_retries_on_429(self, client: OddsApiClient) -> None:
        """收到 429 時應重試，直到成功或超過最大次數。"""
        success_response = MagicMock()
        success_response.status_code = 200
        success_response.headers = {}
        success_response.json.return_value = []

        rate_limited = MagicMock()
        rate_limited.status_code = 429
        rate_limited.headers = {}

        with patch.object(client._session, "get",
                          side_effect=[rate_limited, success_response]):
            with patch("time.sleep"):  # 不真的等待
                result, _ = client._make_request_with_retry("sports", {})
                assert result == []

    def test_retries_on_500(self, client: OddsApiClient) -> None:
        """收到 500 時應重試。"""
        success_response = MagicMock()
        success_response.status_code = 200
        success_response.headers = {}
        success_response.json.return_value = {"data": "ok"}

        server_error = MagicMock()
        server_error.status_code = 500
        server_error.headers = {}

        with patch.object(client._session, "get",
                          side_effect=[server_error, success_response]):
            with patch("time.sleep"):
                result, _ = client._make_request_with_retry("test", {})
                assert result == {"data": "ok"}

    def test_raises_after_max_retries(self, client: OddsApiClient) -> None:
        """超過最大重試次數後應拋出 HTTPError。"""
        error_response = MagicMock()
        error_response.status_code = 500
        error_response.headers = {}

        with patch.object(client._session, "get",
                          return_value=error_response):
            with patch("time.sleep"):
                with pytest.raises(requests.HTTPError):
                    client._make_request_with_retry("test", {})


# ---------------------------------------------------------------------------
# 資料正規化測試
# ---------------------------------------------------------------------------

class TestOddsNormalization:
    """針對 _normalize_odds() 的資料格式轉換測試。"""

    def _make_raw_event(
        self,
        match_id: str = "evt_001",
        home: str = "Lakers",
        away: str = "Celtics",
        bookmakers: list | None = None
    ) -> dict:
        """建立模擬的 API 回應事件。"""
        if bookmakers is None:
            bookmakers = [{
                "key": "draftkings",
                "title": "DraftKings",
                "markets": [{
                    "key": "h2h",
                    "outcomes": [
                        {"name": home, "price": 2.10},
                        {"name": away, "price": 1.80}
                    ]
                }]
            }]
        return {
            "id": match_id,
            "sport_key": "basketball_nba",
            "home_team": home,
            "away_team": away,
            "commence_time": "2025-06-01T18:00:00Z",
            "bookmakers": bookmakers
        }

    def test_basic_normalization(self, client: OddsApiClient) -> None:
        """基本賠率正規化應正確轉換欄位。"""
        raw = [self._make_raw_event()]
        records = client._normalize_odds(raw, "basketball_nba", 100.0)

        assert len(records) == 1
        record = records[0]
        assert isinstance(record, OddsRecord)
        assert record.match_id == "evt_001"
        assert record.home_team == "Lakers"
        assert record.away_team == "Celtics"
        assert record.platform == "draftkings"
        assert record.odds_home == pytest.approx(2.10)
        assert record.odds_away == pytest.approx(1.80)
        assert record.sport == "basketball_nba"
        assert record.latency_ms == pytest.approx(100.0)

    def test_multiple_bookmakers_produce_multiple_records(
        self, client: OddsApiClient
    ) -> None:
        """多個博彩平台應產生多筆 OddsRecord。"""
        raw = [self._make_raw_event(bookmakers=[
            {"key": "draftkings", "markets": [{"key": "h2h", "outcomes": [
                {"name": "Lakers", "price": 2.10},
                {"name": "Celtics", "price": 1.80}
            ]}]},
            {"key": "betmgm", "markets": [{"key": "h2h", "outcomes": [
                {"name": "Lakers", "price": 2.05},
                {"name": "Celtics", "price": 1.85}
            ]}]}
        ])]
        records = client._normalize_odds(raw, "basketball_nba", 50.0)
        assert len(records) == 2
        platforms = {r.platform for r in records}
        assert platforms == {"draftkings", "betmgm"}

    def test_missing_odds_skipped(self, client: OddsApiClient) -> None:
        """缺少主場或客場賠率的記錄應被跳過（不產生 OddsRecord）。"""
        raw = [self._make_raw_event(bookmakers=[{
            "key": "bad_bm",
            "markets": [{"key": "h2h", "outcomes": [
                {"name": "Lakers", "price": 2.10}
                # 缺少 away team
            ]}]
        }])]
        records = client._normalize_odds(raw, "basketball_nba", 100.0)
        assert len(records) == 0

    def test_non_h2h_market_skipped(self, client: OddsApiClient) -> None:
        """非 h2h 市場（如 spreads）應被過濾，不納入記錄。"""
        raw = [self._make_raw_event(bookmakers=[{
            "key": "bm",
            "markets": [{"key": "spreads", "outcomes": [
                {"name": "Lakers", "price": 1.90},
                {"name": "Celtics", "price": 1.90}
            ]}]
        }])]
        records = client._normalize_odds(raw, "basketball_nba", 100.0)
        assert len(records) == 0

    def test_draw_odds_captured_for_soccer(self, client: OddsApiClient) -> None:
        """足球比賽的平局賠率應被正確捕捉至 odds_draw 欄位。"""
        raw = [self._make_raw_event(
            home="Arsenal", away="Chelsea",
            bookmakers=[{
                "key": "bet365",
                "markets": [{"key": "h2h", "outcomes": [
                    {"name": "Arsenal", "price": 2.50},
                    {"name": "Chelsea", "price": 2.80},
                    {"name": "Draw", "price": 3.20}
                ]}]
            }]
        )]
        records = client._normalize_odds(raw, "soccer_epl", 100.0)
        assert len(records) == 1
        assert records[0].odds_draw == pytest.approx(3.20)

    def test_raw_json_preserved(self, client: OddsApiClient) -> None:
        """原始 JSON 應被保存在 raw_json 欄位中（稽核軌跡）。"""
        event = self._make_raw_event()
        records = client._normalize_odds([event], "basketball_nba", 100.0)
        assert records[0].raw_json is not None
        parsed = json.loads(records[0].raw_json)
        assert parsed["id"] == "evt_001"

    def test_commence_time_parsed_correctly(self, client: OddsApiClient) -> None:
        """commence_time 字串應被正確解析為 datetime 物件。"""
        raw = [self._make_raw_event()]
        records = client._normalize_odds(raw, "basketball_nba", 100.0)
        assert records[0].commence_time is not None
        assert isinstance(records[0].commence_time, datetime)


# ====== 自動生成的測試執行區塊 ======
if __name__ == "__main__":
    st.write("---")
    st.subheader("函數測試區塊")
    if st.button("執行 mock_config"):
        try:
            res = mock_config() # 請視需要自行補上參數
            st.write("執行結果:", res)
        except Exception as e:
            st.error(f"執行出錯，可能需要提供參數：{e}")
    if st.button("執行 test_api_config"):
        try:
            res = test_api_config() # 請視需要自行補上參數
            st.write("執行結果:", res)
        except Exception as e:
            st.error(f"執行出錯，可能需要提供參數：{e}")
    if st.button("執行 client"):
        try:
            res = client() # 請視需要自行補上參數
            st.write("執行結果:", res)
        except Exception as e:
            st.error(f"執行出錯，可能需要提供參數：{e}")
