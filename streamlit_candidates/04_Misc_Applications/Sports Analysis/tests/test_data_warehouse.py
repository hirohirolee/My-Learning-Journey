import streamlit as st
st.title('test_data_warehouse.py - 自動化展示')
st.info('這是從原專案腳本自動包裝產生的互動式介面。')

"""
tests/test_data_warehouse.py - OddsDatabase 資料完整性檢查測試

涵蓋：
- data_integrity_check() 的各種合格/不合格情境
- insert_records() 的重複寫入防護
- fetch_all / fetch_since 查詢介面
"""

import sqlite3
import tempfile
import os
from datetime import datetime, timedelta

import pytest

# 測試目標模組
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from data_warehouse import OddsDatabase, IntegrityCheckResult
from data_provider import OddsRecord


# ---------------------------------------------------------------------------
# 共用 Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def temp_db(tmp_path) -> OddsDatabase:
    """每個測試使用獨立的臨時 SQLite 資料庫。"""
    db_path = str(tmp_path / "test_odds.db")
    return OddsDatabase(db_path=db_path, min_valid_odds=1.0, max_valid_odds=10000.0)


def _make_valid_record(**kwargs) -> OddsRecord:
    """建立一筆預設有效的 OddsRecord（方便在測試中覆寫特定欄位）。"""
    defaults = {
        "match_id": "test_match_001",
        "sport": "basketball_nba",
        "home_team": "Lakers",
        "away_team": "Celtics",
        "platform": "draftkings",
        "odds_home": 2.10,
        "odds_away": 1.80,
        "odds_draw": None,
        "timestamp": datetime(2025, 6, 1, 12, 0, 0),
        "latency_ms": 150.0,
        "commence_time": None,
        "raw_json": None,
        "is_valid": 1
    }
    defaults.update(kwargs)
    return OddsRecord(**defaults)


# ---------------------------------------------------------------------------
# data_integrity_check() 測試
# ---------------------------------------------------------------------------

class TestDataIntegrityCheck:
    """針對 data_integrity_check() 的完整邊界條件測試。"""

    def test_valid_record_passes(self, temp_db: OddsDatabase) -> None:
        """合法記錄應通過完整性檢查，is_valid=True，reasons 為空。"""
        record = _make_valid_record()
        result = temp_db.data_integrity_check(record)
        assert result.is_valid is True
        assert result.reasons == []
        assert result.to_invalid_reason() is None

    def test_empty_match_id_fails(self, temp_db: OddsDatabase) -> None:
        """空 match_id 應使 is_valid=False，並記錄原因。"""
        record = _make_valid_record(match_id="")
        result = temp_db.data_integrity_check(record)
        assert result.is_valid is False
        assert any("match_id" in r for r in result.reasons)

    def test_empty_platform_fails(self, temp_db: OddsDatabase) -> None:
        """空 platform 應使 is_valid=False。"""
        record = _make_valid_record(platform="")
        result = temp_db.data_integrity_check(record)
        assert result.is_valid is False
        assert any("platform" in r for r in result.reasons)

    def test_odds_below_min_fails(self, temp_db: OddsDatabase) -> None:
        """賠率 ≤ 1.0（min_valid_odds）應判定為不合格。"""
        record = _make_valid_record(odds_home=0.5)
        result = temp_db.data_integrity_check(record)
        assert result.is_valid is False
        assert any("odds_home" in r for r in result.reasons)

    def test_odds_exactly_at_min_fails(self, temp_db: OddsDatabase) -> None:
        """賠率等於下限（1.0）應判定為不合格（必須大於 1.0）。"""
        record = _make_valid_record(odds_home=1.0)
        result = temp_db.data_integrity_check(record)
        assert result.is_valid is False

    def test_odds_above_max_fails(self, temp_db: OddsDatabase) -> None:
        """賠率超過上限（10000.0）應判定為不合格。"""
        record = _make_valid_record(odds_away=99999.0)
        result = temp_db.data_integrity_check(record)
        assert result.is_valid is False
        assert any("odds_away" in r for r in result.reasons)

    def test_none_timestamp_fails(self, temp_db: OddsDatabase) -> None:
        """timestamp 為 None 應判定為不合格。"""
        record = _make_valid_record(timestamp=None)
        result = temp_db.data_integrity_check(record)
        assert result.is_valid is False
        assert any("timestamp" in r for r in result.reasons)

    def test_negative_latency_fails(self, temp_db: OddsDatabase) -> None:
        """負的 latency_ms 應判定為不合格。"""
        record = _make_valid_record(latency_ms=-1.0)
        result = temp_db.data_integrity_check(record)
        assert result.is_valid is False
        assert any("latency_ms" in r for r in result.reasons)

    def test_multiple_failures_all_recorded(self, temp_db: OddsDatabase) -> None:
        """多個欄位同時不合格時，所有原因都應被記錄（而非短路）。"""
        record = _make_valid_record(match_id="", odds_home=0.1, latency_ms=-5)
        result = temp_db.data_integrity_check(record)
        assert result.is_valid is False
        assert len(result.reasons) >= 2

    def test_draw_odds_validated_when_present(self, temp_db: OddsDatabase) -> None:
        """提供 odds_draw 時，也應執行賠率合理性檢查。"""
        record = _make_valid_record(odds_draw=0.5)
        result = temp_db.data_integrity_check(record)
        assert result.is_valid is False
        assert any("odds_draw" in r for r in result.reasons)

    def test_valid_draw_odds_passes(self, temp_db: OddsDatabase) -> None:
        """合法的 odds_draw 應通過檢查。"""
        record = _make_valid_record(odds_draw=3.50)
        result = temp_db.data_integrity_check(record)
        assert result.is_valid is True


# ---------------------------------------------------------------------------
# insert_records() 測試
# ---------------------------------------------------------------------------

class TestInsertRecords:
    """針對 insert_records() 的功能測試。"""

    def test_insert_valid_record(self, temp_db: OddsDatabase) -> None:
        """寫入一筆有效記錄後，DB 應有一筆資料。"""
        record = _make_valid_record()
        stats = temp_db.insert_records([record])
        assert stats["inserted"] == 1
        assert stats["invalid"] == 0
        assert stats["duplicate"] == 0

    def test_invalid_record_stored_with_flag(self, temp_db: OddsDatabase) -> None:
        """不合格記錄應寫入 DB 但標記 is_valid=0，保留稽核軌跡。"""
        record = _make_valid_record(odds_home=0.0)
        stats = temp_db.insert_records([record])

        # 應寫入 DB（保留稽核軌跡），但標記為 invalid
        assert stats["invalid"] == 1
        all_records = temp_db.fetch_all(valid_only=False)
        assert len(all_records) == 1
        assert all_records[0]["is_valid"] == 0
        assert all_records[0]["invalid_reason"] is not None

    def test_duplicate_record_skipped(self, temp_db: OddsDatabase) -> None:
        """相同 (match_id, platform, timestamp) 的重複記錄應被跳過。"""
        record = _make_valid_record()
        temp_db.insert_records([record])
        stats = temp_db.insert_records([record])
        assert stats["duplicate"] == 1
        assert stats["inserted"] == 0

    def test_different_platform_same_match_both_inserted(
        self, temp_db: OddsDatabase
    ) -> None:
        """同一場賽事但不同平台的記錄，兩筆都應寫入。"""
        record_a = _make_valid_record(platform="draftkings")
        record_b = _make_valid_record(platform="betmgm")
        stats = temp_db.insert_records([record_a, record_b])
        assert stats["inserted"] == 2

    def test_batch_insert_mixed_valid_invalid(self, temp_db: OddsDatabase) -> None:
        """
        批量寫入含有效和無效記錄時：
        - 無效記錄標記 is_valid=0 並仍寫入 DB（保留稽核軌跡）
        - stats["invalid"] 計算被 integrity check 標記為不合格的記錄數
        - stats["inserted"] 計算實際寫入（含有效 + 已標記的無效記錄）
        """
        valid = _make_valid_record()
        invalid = _make_valid_record(
            match_id="test_match_002",
            platform="betmgm",
            odds_home=-1.0
        )
        stats = temp_db.insert_records([valid, invalid])

        # 無效記錄仍被寫入 DB，但標記為 is_valid=0
        assert stats["invalid"] == 1, "應有 1 筆被 integrity check 標記為不合格"
        assert stats["duplicate"] == 0, "無重複記錄"

        # 驗證 DB 中共有 2 筆，但一筆有效一筆無效
        all_records = temp_db.fetch_all(valid_only=False)
        assert len(all_records) == 2, "兩筆都應寫入 DB（稽核軌跡）"
        valid_count = sum(1 for r in all_records if r["is_valid"] == 1)
        invalid_count = sum(1 for r in all_records if r["is_valid"] == 0)
        assert valid_count == 1
        assert invalid_count == 1


# ---------------------------------------------------------------------------
# fetch_all / fetch_since 測試
# ---------------------------------------------------------------------------

class TestQueryInterfaces:
    """針對查詢介面的測試。"""

    def test_fetch_all_returns_all_records(self, temp_db: OddsDatabase) -> None:
        """fetch_all() 應回傳所有記錄（含無效）。"""
        temp_db.insert_records([
            _make_valid_record(),
            _make_valid_record(platform="betmgm")
        ])
        records = temp_db.fetch_all()
        assert len(records) == 2

    def test_fetch_all_valid_only(self, temp_db: OddsDatabase) -> None:
        """fetch_all(valid_only=True) 應僅回傳 is_valid=1 的記錄。"""
        temp_db.insert_records([
            _make_valid_record(),
            _make_valid_record(
                match_id="bad_match",
                platform="betmgm",
                odds_home=0.1
            )
        ])
        records = temp_db.fetch_all(valid_only=True)
        assert all(r["is_valid"] == 1 for r in records)

    def test_fetch_since_filters_by_timestamp(self, temp_db: OddsDatabase) -> None:
        """fetch_since() 應只回傳指定時間點之後的記錄。"""
        early = _make_valid_record(
            timestamp=datetime(2025, 1, 1, 0, 0, 0),
            platform="draftkings"
        )
        late = _make_valid_record(
            timestamp=datetime(2025, 6, 1, 0, 0, 0),
            platform="betmgm"
        )
        temp_db.insert_records([early, late])

        cutoff = datetime(2025, 3, 1, 0, 0, 0)
        records = temp_db.fetch_since(cutoff)
        assert len(records) == 1
        assert "betmgm" in records[0]["platform"]

    def test_empty_db_returns_empty_list(self, temp_db: OddsDatabase) -> None:
        """空資料庫的 fetch_all() 應回傳空列表。"""
        records = temp_db.fetch_all()
        assert records == []


# ====== 自動生成的測試執行區塊 ======
if __name__ == "__main__":
    st.write("---")
    st.subheader("函數測試區塊")
    if st.button("執行 temp_db"):
        try:
            res = temp_db() # 請視需要自行補上參數
            st.write("執行結果:", res)
        except Exception as e:
            st.error(f"執行出錯，可能需要提供參數：{e}")
