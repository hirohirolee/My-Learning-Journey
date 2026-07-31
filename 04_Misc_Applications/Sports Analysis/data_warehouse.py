"""
data_warehouse.py - SQLite 資料倉儲管理器

封裝所有與 SQLite 資料庫的互動，包含：
- Schema 建立與遷移
- 資料完整性檢查（寫入前驗證，不合格資料標記 is_valid=0 而非丟棄）
- 資料寫入（唯一性約束防重複）
- 資料查詢介面（fetch_all / fetch_since）
"""

import logging
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Generator, Optional

from data_provider import OddsRecord

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Schema 定義（DDL）
# ---------------------------------------------------------------------------

SCHEMA_DDL = """
-- 賠率快照主表（Fact Table）
CREATE TABLE IF NOT EXISTS odds_snapshots (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id      TEXT    NOT NULL,
    sport         TEXT    NOT NULL,
    platform      TEXT    NOT NULL,
    home_team     TEXT    NOT NULL,
    away_team     TEXT    NOT NULL,
    odds_home     REAL    NOT NULL,
    odds_away     REAL    NOT NULL,
    odds_draw     REAL,
    timestamp     TEXT    NOT NULL,  -- ISO 8601 UTC
    commence_time TEXT,              -- ISO 8601 UTC
    latency_ms    REAL    NOT NULL,
    is_valid      INTEGER NOT NULL DEFAULT 1,  -- 1=有效, 0=資料異常
    invalid_reason TEXT,             -- is_valid=0 時記錄原因
    anomaly_flag  INTEGER DEFAULT 0, -- 分析引擎標記的異常點

    -- 唯一性約束：同一場賽事、同一平台、同一時間戳只能有一筆記錄
    UNIQUE (match_id, platform, timestamp)
);

-- 建立查詢常用欄位的複合索引
CREATE INDEX IF NOT EXISTS idx_match_platform
    ON odds_snapshots (match_id, platform);

CREATE INDEX IF NOT EXISTS idx_timestamp
    ON odds_snapshots (timestamp);

CREATE INDEX IF NOT EXISTS idx_sport_timestamp
    ON odds_snapshots (sport, timestamp);

-- 稽核日誌表（記錄每次資料完整性檢查結果）
CREATE TABLE IF NOT EXISTS audit_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    checked_at      TEXT    NOT NULL,  -- ISO 8601 UTC
    total_checked   INTEGER NOT NULL,
    valid_count     INTEGER NOT NULL,
    invalid_count   INTEGER NOT NULL,
    duplicate_count INTEGER NOT NULL,
    notes           TEXT
);
"""

# ---------------------------------------------------------------------------
# 完整性檢查結果
# ---------------------------------------------------------------------------

@dataclass
class IntegrityCheckResult:
    """資料完整性檢查的詳細結果報告。"""
    is_valid: bool
    reasons: list[str]

    def to_invalid_reason(self) -> Optional[str]:
        """若為無效資料，回傳原因字串；否則回傳 None。"""
        return "; ".join(self.reasons) if self.reasons else None


# ---------------------------------------------------------------------------
# 資料倉儲類別
# ---------------------------------------------------------------------------

class OddsDatabase:
    """
    SQLite 賠率資料倉儲。

    使用 context manager 管理連線生命週期，
    透過唯一性約束（match_id, platform, timestamp）防止重複寫入。
    """

    def __init__(self, db_path: str, min_valid_odds: float = 1.0,
                 max_valid_odds: float = 10000.0) -> None:
        """
        初始化資料庫連線並建立 Schema。

        Args:
            db_path:       SQLite 資料庫檔案路徑
            min_valid_odds: 賠率合理下限（用於完整性檢查）
            max_valid_odds: 賠率合理上限（用於完整性檢查）
        """
        self._db_path = Path(db_path)
        self._min_valid_odds = min_valid_odds
        self._max_valid_odds = max_valid_odds

        # 自動建立目錄
        self._db_path.parent.mkdir(parents=True, exist_ok=True)

        self._init_schema()
        logger.info("OddsDatabase 初始化完成：%s", self._db_path.resolve())

    @contextmanager
    def _get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """
        Context Manager：取得資料庫連線。

        自動處理 commit（成功）與 rollback（例外），
        確保每次操作結束後連線正確關閉。
        """
        conn = sqlite3.connect(str(self._db_path))
        conn.row_factory = sqlite3.Row  # 允許以欄位名稱存取結果
        conn.execute("PRAGMA journal_mode=WAL;")   # 提升並發寫入效能
        conn.execute("PRAGMA foreign_keys=ON;")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_schema(self) -> None:
        """建立資料表與索引（若已存在則跳過）。"""
        with self._get_connection() as conn:
            conn.executescript(SCHEMA_DDL)
        logger.debug("資料庫 Schema 已確認/建立。")

    # ------------------------------------------------------------------
    # 資料完整性檢查
    # ------------------------------------------------------------------

    def data_integrity_check(self, record: OddsRecord) -> IntegrityCheckResult:
        """
        寫入前對單筆 OddsRecord 執行資料完整性檢查。

        檢查項目：
        1. 必要欄位不得為 None 或空字串
        2. 賠率必須為正數且在合理範圍內
        3. 時間戳不得為 None

        不合格資料會被標記 is_valid=0 並記錄原因，
        而非直接丟棄，保留完整稽核軌跡。

        Args:
            record: 待檢查的 OddsRecord

        Returns:
            IntegrityCheckResult 包含 is_valid 旗標與失敗原因列表
        """
        reasons: list[str] = []

        # 1. 必要字串欄位非空檢查
        required_str_fields = {
            "match_id": record.match_id,
            "sport": record.sport,
            "home_team": record.home_team,
            "away_team": record.away_team,
            "platform": record.platform
        }
        for field_name, value in required_str_fields.items():
            if not value or not str(value).strip():
                reasons.append(f"必要欄位 '{field_name}' 為空或 None")

        # 2. 賠率合理性檢查
        def check_odds(name: str, value: Optional[float]) -> None:
            if value is None:
                reasons.append(f"'{name}' 為 None")
                return
            if not isinstance(value, (int, float)):
                reasons.append(f"'{name}' 非數值型別：{type(value)}")
                return
            if value <= self._min_valid_odds:
                reasons.append(
                    f"'{name}' = {value} 小於或等於下限 {self._min_valid_odds}"
                )
            if value > self._max_valid_odds:
                reasons.append(
                    f"'{name}' = {value} 超過上限 {self._max_valid_odds}"
                )

        check_odds("odds_home", record.odds_home)
        check_odds("odds_away", record.odds_away)
        if record.odds_draw is not None:
            check_odds("odds_draw", record.odds_draw)

        # 3. 時間戳非空檢查
        if record.timestamp is None:
            reasons.append("'timestamp' 為 None")

        # 4. latency_ms 合理性
        if record.latency_ms < 0:
            reasons.append(f"'latency_ms' = {record.latency_ms} 不可為負數")

        is_valid = len(reasons) == 0
        if not is_valid:
            logger.warning(
                "資料完整性檢查不通過 [match_id=%s, platform=%s]：%s",
                record.match_id, record.platform, "; ".join(reasons)
            )

        return IntegrityCheckResult(is_valid=is_valid, reasons=reasons)

    # ------------------------------------------------------------------
    # 資料寫入
    # ------------------------------------------------------------------

    def insert_records(self, records: list[OddsRecord]) -> dict[str, int]:
        """
        批量寫入 OddsRecord 至資料庫。

        流程：
        1. 每筆執行 data_integrity_check()
        2. 不合格者設 is_valid=0，照常寫入（保留稽核軌跡）
        3. 違反唯一性約束的重複記錄以 INSERT OR IGNORE 跳過

        Args:
            records: 待寫入的 OddsRecord 列表

        Returns:
            統計 dict：{"inserted", "invalid", "duplicate"}
        """
        stats = {"inserted": 0, "invalid": 0, "duplicate": 0}

        with self._get_connection() as conn:
            for record in records:
                integrity = self.data_integrity_check(record)

                is_valid = 1 if integrity.is_valid else 0
                invalid_reason = integrity.to_invalid_reason()

                # 標記不合格記錄
                if not integrity.is_valid:
                    stats["invalid"] += 1

                try:
                    conn.execute(
                        """
                        INSERT OR IGNORE INTO odds_snapshots (
                            match_id, sport, platform, home_team, away_team,
                            odds_home, odds_away, odds_draw,
                            timestamp, commence_time, latency_ms,
                            is_valid, invalid_reason
                        ) VALUES (
                            :match_id, :sport, :platform, :home_team, :away_team,
                            :odds_home, :odds_away, :odds_draw,
                            :timestamp, :commence_time, :latency_ms,
                            :is_valid, :invalid_reason
                        )
                        """,
                        {
                            "match_id": record.match_id,
                            "sport": record.sport,
                            "platform": record.platform,
                            "home_team": record.home_team,
                            "away_team": record.away_team,
                            "odds_home": record.odds_home,
                            "odds_away": record.odds_away,
                            "odds_draw": record.odds_draw,
                            "timestamp": record.timestamp.isoformat()
                            if isinstance(record.timestamp, datetime)
                            else record.timestamp,
                            "commence_time": record.commence_time.isoformat()
                            if isinstance(record.commence_time, datetime)
                            else record.commence_time,
                            "latency_ms": record.latency_ms,
                            "is_valid": is_valid,
                            "invalid_reason": invalid_reason
                        }
                    )
                    # INSERT OR IGNORE：若 rowcount=0 表示因唯一性約束被跳過
                    if conn.execute("SELECT changes()").fetchone()[0] == 0:
                        stats["duplicate"] += 1
                    else:
                        stats["inserted"] += 1

                except sqlite3.Error as exc:
                    logger.error(
                        "寫入記錄失敗 [match_id=%s, platform=%s]：%s",
                        record.match_id, record.platform, exc
                    )

            # 寫入稽核日誌
            self._write_audit_log(conn, stats, len(records))

        logger.info(
            "寫入完成：%d 筆成功，%d 筆不合格（已標記），%d 筆重複（已略過）。",
            stats["inserted"], stats["invalid"], stats["duplicate"]
        )
        return stats

    def _write_audit_log(
        self,
        conn: sqlite3.Connection,
        stats: dict[str, int],
        total: int
    ) -> None:
        """
        將本次寫入操作的稽核摘要記錄至 audit_log 表。

        Args:
            conn:  資料庫連線
            stats: 寫入統計
            total: 總記錄數
        """
        conn.execute(
            """
            INSERT INTO audit_log
                (checked_at, total_checked, valid_count, invalid_count,
                 duplicate_count, notes)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.utcnow().isoformat(),
                total,
                stats.get("inserted", 0),
                stats.get("invalid", 0),
                stats.get("duplicate", 0),
                None
            )
        )

    # ------------------------------------------------------------------
    # 資料查詢介面
    # ------------------------------------------------------------------

    def fetch_all(
        self,
        valid_only: bool = False
    ) -> list[dict[str, Any]]:
        """
        取得資料庫中所有賠率快照記錄。

        Args:
            valid_only: 若為 True，僅回傳 is_valid=1 的記錄

        Returns:
            dict 列表（每筆記錄為一個 dict，欄位名稱對應資料表欄位）
        """
        query = "SELECT * FROM odds_snapshots"
        params: list[Any] = []
        if valid_only:
            query += " WHERE is_valid = 1"
        query += " ORDER BY timestamp DESC"

        with self._get_connection() as conn:
            cursor = conn.execute(query, params)
            rows = [dict(row) for row in cursor.fetchall()]

        logger.debug("fetch_all 回傳 %d 筆記錄。", len(rows))
        return rows

    def fetch_since(
        self,
        since_timestamp: datetime,
        valid_only: bool = False
    ) -> list[dict[str, Any]]:
        """
        取得指定時間點之後的賠率快照記錄。

        Args:
            since_timestamp: 查詢起始時間（UTC datetime）
            valid_only:      若為 True，僅回傳有效記錄

        Returns:
            dict 列表（依時間正序排列）
        """
        query = "SELECT * FROM odds_snapshots WHERE timestamp >= ?"
        params: list[Any] = [since_timestamp.isoformat()]

        if valid_only:
            query += " AND is_valid = 1"
        query += " ORDER BY timestamp ASC"

        with self._get_connection() as conn:
            cursor = conn.execute(query, params)
            rows = [dict(row) for row in cursor.fetchall()]

        logger.debug(
            "fetch_since(%s) 回傳 %d 筆記錄。",
            since_timestamp.isoformat(), len(rows)
        )
        return rows

    def fetch_by_match(self, match_id: str) -> list[dict[str, Any]]:
        """
        取得指定賽事的所有平台賠率快照。

        Args:
            match_id: 賽事唯一識別碼

        Returns:
            dict 列表
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM odds_snapshots WHERE match_id = ? "
                "ORDER BY platform, timestamp",
                (match_id,)
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_summary_stats(self) -> dict[str, Any]:
        """
        取得資料倉儲的統計摘要。

        Returns:
            包含總記錄數、有效/無效比例、覆蓋運動項目等資訊的 dict
        """
        with self._get_connection() as conn:
            total = conn.execute(
                "SELECT COUNT(*) FROM odds_snapshots"
            ).fetchone()[0]
            valid = conn.execute(
                "SELECT COUNT(*) FROM odds_snapshots WHERE is_valid = 1"
            ).fetchone()[0]
            sports = conn.execute(
                "SELECT DISTINCT sport FROM odds_snapshots"
            ).fetchall()
            platforms = conn.execute(
                "SELECT DISTINCT platform FROM odds_snapshots"
            ).fetchall()
            latest_ts = conn.execute(
                "SELECT MAX(timestamp) FROM odds_snapshots"
            ).fetchone()[0]

        return {
            "total_records": total,
            "valid_records": valid,
            "invalid_records": total - valid,
            "sports": [row[0] for row in sports],
            "platforms": [row[0] for row in platforms],
            "latest_timestamp": latest_ts
        }
