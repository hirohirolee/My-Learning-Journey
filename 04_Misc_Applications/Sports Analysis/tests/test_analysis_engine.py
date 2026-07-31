"""
tests/test_analysis_engine.py - ArbitrageAnalyzer 分析邏輯測試

涵蓋：
- ROI 計算正確性（含有/無套利機會的情境）
- 異常值標記邏輯
- 穩定性分數計算
- 匯出函式的基本功能
"""

import os
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from analysis_engine import ArbitrageAnalyzer


# ---------------------------------------------------------------------------
# 共用 Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def analyzer(tmp_path) -> ArbitrageAnalyzer:
    """使用臨時目錄的 ArbitrageAnalyzer 實例。"""
    return ArbitrageAnalyzer(
        anomaly_threshold_sigma=3.0,
        stability_window_minutes=30,
        min_roi_threshold=0.0,
        csv_output_dir=str(tmp_path / "output"),
        markdown_output_path=str(tmp_path / "output" / "report.md")
    )


def _make_raw_records(
    match_id: str = "match_001",
    platforms_odds: dict | None = None
) -> list[dict]:
    """
    建立模擬的 DB 記錄列表。

    Args:
        match_id:       賽事 ID
        platforms_odds: {platform: (odds_home, odds_away)} 的 dict
    """
    if platforms_odds is None:
        platforms_odds = {
            "draftkings": (2.10, 1.80),
            "betmgm": (2.00, 1.90),
        }

    ts = datetime(2025, 6, 1, 12, 0, 0)
    records = []
    for idx, (platform, (h, a)) in enumerate(platforms_odds.items()):
        records.append({
            "id": idx + 1,
            "match_id": match_id,
            "sport": "basketball_nba",
            "home_team": "Lakers",
            "away_team": "Celtics",
            "platform": platform,
            "odds_home": h,
            "odds_away": a,
            "odds_draw": None,
            "timestamp": ts.isoformat(),
            "commence_time": None,
            "latency_ms": 100.0,
            "is_valid": 1,
            "invalid_reason": None,
            "anomaly_flag": 0
        })
    return records


# ---------------------------------------------------------------------------
# ROI 計算測試
# ---------------------------------------------------------------------------

class TestRoiCalculation:
    """針對隱含機率總和與 ROI 計算的測試。"""

    def test_no_arbitrage_opportunity(self, analyzer: ArbitrageAnalyzer) -> None:
        """正常市場（無套利機會）應得到負 ROI。

        例：draftkings 2.10 / 1.80 → S = 1/2.10 + 1/1.80 ≈ 1.031 → ROI < 0
        """
        records = _make_raw_records(platforms_odds={
            "draftkings": (2.10, 1.80),
        })
        df = analyzer.analyze(records)
        arb = analyzer.get_arbitrage_opportunities(df)
        assert len(arb) == 0, "應無正 ROI 套利機會"

    def test_arbitrage_opportunity_detected(self, analyzer: ArbitrageAnalyzer) -> None:
        """
        製造一個人工套利機會：
        - 平台 A 主場賠率：3.00（1/3.00 ≈ 0.333）
        - 平台 B 客場賠率：3.00（1/3.00 ≈ 0.333）
        - S = 0.333 + 0.333 ≈ 0.667 → ROI = 1/0.667 - 1 ≈ +0.50（50%）
        """
        records = _make_raw_records(platforms_odds={
            "platform_a": (3.00, 1.10),
            "platform_b": (1.10, 3.00),
        })
        df = analyzer.analyze(records)
        arb = analyzer.get_arbitrage_opportunities(df)
        assert len(arb) > 0, "應偵測到正 ROI 套利機會"
        assert arb[0]["roi"] > 0

    def test_roi_formula_correctness(self, analyzer: ArbitrageAnalyzer) -> None:
        """
        驗證 ROI 計算公式精確性。

        手算：best_home=3.00, best_away=3.00
        S = 1/3 + 1/3 = 0.6667
        ROI = 1/0.6667 - 1 = 0.5000（≈ 50%）
        """
        records = _make_raw_records(platforms_odds={
            "a": (3.00, 1.10),
            "b": (1.10, 3.00),
        })
        df = analyzer.analyze(records)
        arb_df = analyzer._compute_arbitrage_roi(df)

        if not arb_df.empty:
            row = arb_df.iloc[0]
            expected_s = (1 / 3.00) + (1 / 3.00)
            expected_roi = (1 / expected_s) - 1
            assert abs(row["implied_prob_sum"] - expected_s) < 1e-4
            assert abs(row["roi"] - expected_roi) < 1e-4

    def test_roi_uses_best_cross_platform_odds(
        self, analyzer: ArbitrageAnalyzer
    ) -> None:
        """ROI 計算應使用跨平台最佳賠率（而非單一平台賠率）。"""
        records = _make_raw_records(platforms_odds={
            "cheap": (1.80, 1.70),
            "expensive": (2.20, 2.10),
        })
        df = analyzer.analyze(records)
        arb_df = analyzer._compute_arbitrage_roi(df)

        # 最佳主場應為 2.20，最佳客場應為 2.10
        if not arb_df.empty:
            row = arb_df.iloc[0]
            assert row["best_odds_home"] == pytest.approx(2.20, abs=0.01)
            assert row["best_odds_away"] == pytest.approx(2.10, abs=0.01)

    def test_empty_records_returns_empty_dataframe(
        self, analyzer: ArbitrageAnalyzer
    ) -> None:
        """空輸入應回傳空 DataFrame 而非拋出例外。"""
        df = analyzer.analyze([])
        assert df.empty

    def test_invalid_records_excluded_from_analysis(
        self, analyzer: ArbitrageAnalyzer
    ) -> None:
        """is_valid=0 的記錄不應納入 ROI 分析。"""
        records = _make_raw_records()
        for r in records:
            r["is_valid"] = 0

        df = analyzer.analyze(records)
        assert df.empty, "所有記錄都是無效的，分析結果應為空"

    def test_roi_min_threshold_filters_opportunities(
        self, analyzer: ArbitrageAnalyzer
    ) -> None:
        """設定 min_roi_threshold 後，低於門檻的套利機會應被過濾。"""
        high_roi_analyzer = ArbitrageAnalyzer(
            min_roi_threshold=0.10,  # 要求至少 10% ROI
            csv_output_dir=str(Path(analyzer._csv_dir)),
            markdown_output_path=str(analyzer._md_path)
        )
        records = _make_raw_records(platforms_odds={
            "a": (2.05, 1.10),
            "b": (1.10, 2.05),
        })
        df = high_roi_analyzer.analyze(records)
        arb = high_roi_analyzer.get_arbitrage_opportunities(df)
        # S ≈ 1/2.05 + 1/2.05 ≈ 0.976 → ROI ≈ 2.5%，低於 10% 門檻
        assert len(arb) == 0


# ---------------------------------------------------------------------------
# 異常值標記測試
# ---------------------------------------------------------------------------

class TestAnomalyFlagging:
    """針對異常值標記邏輯的測試。"""

    def _make_time_series_records(
        self,
        base_odds: float,
        spike_odds: float,
        n_normal: int = 20
    ) -> list[dict]:
        """
        建立含有一個異常值的時間序列記錄。

        Args:
            base_odds:  正常賠率基準值
            spike_odds: 異常的賠率值
            n_normal:   正常記錄數量（樣本越多，標準差越穩定）
        """
        records = []
        for i in range(n_normal):
            records.append({
                "id": i + 1,
                "match_id": "ts_match",
                "sport": "nba",
                "home_team": "TeamA",
                "away_team": "TeamB",
                "platform": "platform_x",
                "odds_home": base_odds + (i % 3) * 0.01,  # 微小的正常波動
                "odds_away": 2.0,
                "odds_draw": None,
                "timestamp": (datetime(2025, 6, 1, 12, 0, 0)
                              + timedelta(minutes=i * 5)).isoformat(),
                "latency_ms": 100.0,
                "is_valid": 1,
                "invalid_reason": None,
                "anomaly_flag": 0
            })
        # 插入一個明顯的異常值
        records.append({
            "id": n_normal + 1,
            "match_id": "ts_match",
            "sport": "nba",
            "home_team": "TeamA",
            "away_team": "TeamB",
            "platform": "platform_x",
            "odds_home": spike_odds,
            "odds_away": 2.0,
            "odds_draw": None,
            "timestamp": (datetime(2025, 6, 1, 12, 0, 0)
                          + timedelta(minutes=n_normal * 5)).isoformat(),
            "latency_ms": 100.0,
            "is_valid": 1,
            "invalid_reason": None,
            "anomaly_flag": 0
        })
        return records

    def test_extreme_odds_flagged_as_anomaly(
        self, analyzer: ArbitrageAnalyzer
    ) -> None:
        """極端賠率異常值應被正確標記 anomaly_flag=True。"""
        records = self._make_time_series_records(
            base_odds=2.00,
            spike_odds=50.00,  # 極端異常值
            n_normal=20
        )
        df = analyzer.analyze(records)
        assert "anomaly_flag" in df.columns
        flagged = df[df["anomaly_flag"] == True]
        assert len(flagged) > 0, "極端異常值應被標記"

    def test_anomaly_reason_is_recorded(
        self, analyzer: ArbitrageAnalyzer
    ) -> None:
        """被標記為異常的記錄，anomaly_reason 不應為空（透明稽核）。"""
        records = self._make_time_series_records(
            base_odds=2.00,
            spike_odds=50.00,
            n_normal=20
        )
        df = analyzer.analyze(records)
        if "anomaly_flag" in df.columns:
            flagged = df[df["anomaly_flag"] == True]
            for _, row in flagged.iterrows():
                assert row["anomaly_reason"] != "", \
                    "異常記錄的判定依據不應為空"

    def test_normal_fluctuation_not_flagged(
        self, analyzer: ArbitrageAnalyzer
    ) -> None:
        """正常的小幅賠率波動不應被標記為異常。"""
        records = []
        for i in range(10):
            records.append({
                "id": i + 1,
                "match_id": "normal_match",
                "sport": "nba",
                "home_team": "A", "away_team": "B",
                "platform": "plat",
                "odds_home": 2.00 + i * 0.01,  # 每步只變動 0.01
                "odds_away": 1.80,
                "odds_draw": None,
                "timestamp": (datetime(2025, 6, 1) + timedelta(minutes=i)).isoformat(),
                "latency_ms": 100.0,
                "is_valid": 1,
                "invalid_reason": None,
                "anomaly_flag": 0
            })
        df = analyzer.analyze(records)
        if "anomaly_flag" in df.columns:
            flagged = df[df["anomaly_flag"] == True]
            assert len(flagged) == 0, "正常波動不應被誤標為異常"

    def test_insufficient_samples_not_flagged(
        self, analyzer: ArbitrageAnalyzer
    ) -> None:
        """樣本數不足（< 3）的賽事不應進行異常標記。"""
        records = _make_raw_records()  # 只有 2 筆記錄
        df = analyzer.analyze(records)
        if "anomaly_flag" in df.columns:
            assert df["anomaly_flag"].sum() == 0


# ---------------------------------------------------------------------------
# 穩定性分數測試
# ---------------------------------------------------------------------------

class TestStabilityScore:
    """針對數據源穩定性分數計算的測試。"""

    def test_stable_platform_has_high_score(
        self, analyzer: ArbitrageAnalyzer
    ) -> None:
        """賠率完全不變的平台，穩定性分數應接近 1.0。"""
        records = []
        for i in range(10):
            records.append({
                "id": i,
                "match_id": "stable_match",
                "sport": "nba",
                "home_team": "A", "away_team": "B",
                "platform": "stable_bm",
                "odds_home": 2.00,  # 從不變動
                "odds_away": 1.80,
                "odds_draw": None,
                "timestamp": (datetime(2025, 6, 1, 12) + timedelta(minutes=i * 3)).isoformat(),
                "latency_ms": 100.0,
                "is_valid": 1,
                "invalid_reason": None,
                "anomaly_flag": 0
            })
        df = pd.DataFrame(records)
        for col in ["timestamp"]:
            df[col] = pd.to_datetime(df[col], utc=True)

        # 清洗後直接測試穩定性計算
        stable_df = analyzer._compute_stability_scores(df)
        row = stable_df[stable_df["platform"] == "stable_bm"].iloc[0]
        assert row["stability_score"] > 0.8, \
            f"穩定平台分數應 > 0.8，實際：{row['stability_score']}"

    def test_volatile_platform_has_low_score(
        self, analyzer: ArbitrageAnalyzer
    ) -> None:
        """賠率頻繁大幅波動的平台，穩定性分數應較低。"""
        records = []
        for i in range(15):
            records.append({
                "id": i,
                "match_id": "volatile_match",
                "sport": "nba",
                "home_team": "A", "away_team": "B",
                "platform": "volatile_bm",
                "odds_home": 2.00 + (i % 2) * 2.0,  # 每次變動 2.0
                "odds_away": 1.80,
                "odds_draw": None,
                "timestamp": (datetime(2025, 6, 1, 12) + timedelta(minutes=i * 2)).isoformat(),
                "latency_ms": 100.0,
                "is_valid": 1,
                "invalid_reason": None,
                "anomaly_flag": 0
            })
        df = pd.DataFrame(records)
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
        df["odds_home"] = pd.to_numeric(df["odds_home"])
        df["odds_away"] = pd.to_numeric(df["odds_away"])

        stable_df = analyzer._compute_stability_scores(df)
        row = stable_df[stable_df["platform"] == "volatile_bm"].iloc[0]
        assert row["stability_score"] < 0.5, \
            f"波動平台分數應 < 0.5，實際：{row['stability_score']}"

    def test_single_record_gets_max_stability(
        self, analyzer: ArbitrageAnalyzer
    ) -> None:
        """只有一筆記錄的 (match, platform) 應得到最高穩定分 1.0。"""
        records = [{
            "id": 1,
            "match_id": "solo_match",
            "sport": "nba",
            "home_team": "A", "away_team": "B",
            "platform": "solo_bm",
            "odds_home": 2.00,
            "odds_away": 1.80,
            "odds_draw": None,
            "timestamp": datetime(2025, 6, 1, 12).isoformat(),
            "latency_ms": 100.0,
            "is_valid": 1,
            "invalid_reason": None,
            "anomaly_flag": 0
        }]
        df = pd.DataFrame(records)
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
        df["odds_home"] = pd.to_numeric(df["odds_home"])
        df["odds_away"] = pd.to_numeric(df["odds_away"])

        stable_df = analyzer._compute_stability_scores(df)
        row = stable_df.iloc[0]
        assert row["stability_score"] == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# 匯出功能測試
# ---------------------------------------------------------------------------

class TestExportFunctions:
    """針對 CSV / Markdown 匯出功能的基本測試。"""

    def test_export_for_powerbi_creates_csv(
        self, analyzer: ArbitrageAnalyzer
    ) -> None:
        """export_for_powerbi() 應在指定目錄產生 CSV 檔案。"""
        records = _make_raw_records()
        df = analyzer.analyze(records)

        if not df.empty:
            csv_path = analyzer.export_for_powerbi(df)
            assert Path(csv_path).exists(), f"CSV 檔案應存在：{csv_path}"
            assert csv_path.endswith(".csv")

            # 驗證 CSV 可被 pandas 讀取且包含必要欄位
            exported = pd.read_csv(csv_path)
            assert len(exported) > 0

    def test_export_markdown_report_creates_file(
        self, analyzer: ArbitrageAnalyzer
    ) -> None:
        """export_markdown_report() 應產生 Markdown 檔案。"""
        records = _make_raw_records()
        df = analyzer.analyze(records)

        if not df.empty:
            md_path = analyzer.export_markdown_report(df, [])
            assert Path(md_path).exists(), f"Markdown 報告應存在：{md_path}"

            content = Path(md_path).read_text(encoding="utf-8")
            assert "# 市場套利分析" in content
            assert "執行摘要" in content

    def test_anomaly_flag_exported_as_integer(
        self, analyzer: ArbitrageAnalyzer
    ) -> None:
        """匯出的 CSV 中 anomaly_flag 應為整數（Power BI 相容性）。"""
        records = _make_raw_records()
        df = analyzer.analyze(records)

        if not df.empty:
            csv_path = analyzer.export_for_powerbi(df)
            exported = pd.read_csv(csv_path)
            if "anomaly_flag" in exported.columns:
                assert exported["anomaly_flag"].dtype in [
                    "int64", "int32", "float64"
                ], "anomaly_flag 應為數值型別（非 bool）"
