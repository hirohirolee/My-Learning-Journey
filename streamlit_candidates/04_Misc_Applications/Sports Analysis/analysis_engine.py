import streamlit as st

"""
analysis_engine.py - 套利分析與資訊效率稽核引擎

核心功能：
1. 跨平台隱含機率總和計算（S = Σ 1/odds_i）
2. ROI 計算（ROI = 1/S - 1），篩選正 ROI 組合
3. 數據源穩定性分數（30 分鐘滾動視窗賠率變動分析）
4. 異常值標記（賠率變動超過 N 倍標準差）
5. 輸出 CSV（Power BI 就緒）與 Markdown 報告
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 套利機會結構
# ---------------------------------------------------------------------------

@dataclass
class ArbitrageOpportunity:
    """單一套利機會的計算結果。"""
    match_id: str
    home_team: str
    away_team: str
    sport: str
    best_odds_home: float         # 跨平台最佳主場賠率
    best_odds_away: float         # 跨平台最佳客場賠率
    best_odds_draw: Optional[float]
    platform_home: str            # 最佳主場賠率的平台
    platform_away: str            # 最佳客場賠率的平台
    implied_prob_sum: float       # S = Σ(1/odds_i)
    roi: float                    # ROI = 1/S - 1
    snapshot_timestamp: str       # 計算基準時間
    has_draw_market: bool = False


# ---------------------------------------------------------------------------
# 分析引擎
# ---------------------------------------------------------------------------

class ArbitrageAnalyzer:
    """
    套利分析與資訊效率稽核引擎。

    以 pandas DataFrame 為核心計算工具，讀取 SQLite 資料後進行：
    - 跨平台賠率比較
    - 隱含機率總和與 ROI 計算
    - 數據源穩定性評分
    - 異常值檢測與標記
    """

    def __init__(
        self,
        anomaly_threshold_sigma: float = 3.0,
        stability_window_minutes: int = 30,
        min_roi_threshold: float = 0.0,
        csv_output_dir: str = "./output",
        markdown_output_path: str = "./output/report.md"
    ) -> None:
        """
        初始化分析引擎。

        Args:
            anomaly_threshold_sigma:    異常值門檻（標準差倍數，預設 3.0）
            stability_window_minutes:   穩定性評分滾動視窗（分鐘，預設 30）
            min_roi_threshold:          最低 ROI 輸出門檻（預設 0.0，即正 ROI）
            csv_output_dir:             CSV 輸出目錄
            markdown_output_path:       Markdown 報告路徑
        """
        self._anomaly_sigma = anomaly_threshold_sigma
        self._stability_window = stability_window_minutes
        self._min_roi = min_roi_threshold
        self._csv_dir = Path(csv_output_dir)
        self._md_path = Path(markdown_output_path)

        # 確保輸出目錄存在
        self._csv_dir.mkdir(parents=True, exist_ok=True)
        self._md_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(
            "ArbitrageAnalyzer 初始化 | 異常門檻：%.1fσ | 穩定視窗：%d 分鐘 | "
            "ROI 門檻：%.2f%%",
            anomaly_threshold_sigma, stability_window_minutes,
            min_roi_threshold * 100
        )

    # ------------------------------------------------------------------
    # 主要分析流程
    # ------------------------------------------------------------------

    def analyze(self, raw_records: list[dict[str, Any]]) -> pd.DataFrame:
        """
        執行完整分析流程，回傳帶有分析欄位的 DataFrame。

        流程：
        1. 載入並清洗資料
        2. 計算穩定性分數（每個 match_id × platform）
        3. 計算跨平台隱含機率總和與 ROI
        4. 標記異常值

        Args:
            raw_records: 來自 OddsDatabase.fetch_all() 的 dict 列表

        Returns:
            分析完成的 DataFrame（含 anomaly_flag、stability_score、roi 等欄位）
        """
        if not raw_records:
            logger.warning("輸入資料為空，返回空 DataFrame。")
            return pd.DataFrame()

        df = self._load_and_clean(raw_records)
        logger.info("載入 %d 筆有效賠率快照。", len(df))

        # 清洗後若無有效資料，直接回傳空 DataFrame
        if df.empty:
            logger.warning("清洗後無有效記錄（所有記錄可能都是 is_valid=0）。")
            return pd.DataFrame()

        # Step 1: 計算穩定性分數
        stability_df = self._compute_stability_scores(df)
        df = df.merge(stability_df, on=["match_id", "platform"], how="left")
        df["stability_score"] = df["stability_score"].fillna(1.0)

        # Step 2: 異常值標記
        df = self._flag_anomalies(df)

        # Step 3: 計算套利 ROI
        arbitrage_df = self._compute_arbitrage_roi(df)

        # Step 4: 合併 ROI 資訊回主 DataFrame
        df = df.merge(
            arbitrage_df[["match_id", "implied_prob_sum", "roi",
                          "has_arb_opportunity"]],
            on="match_id",
            how="left"
        )

        logger.info(
            "分析完成：%d 筆記錄，%d 個套利機會，%d 個異常點。",
            len(df),
            df["has_arb_opportunity"].sum() if "has_arb_opportunity" in df.columns else 0,
            df["anomaly_flag"].sum() if "anomaly_flag" in df.columns else 0
        )
        return df

    def _load_and_clean(self, raw_records: list[dict[str, Any]]) -> pd.DataFrame:
        """
        載入原始記錄並執行基本清洗。

        - 僅保留 is_valid=1 的記錄（無效記錄已保留在 DB 供稽核，不納入分析）
        - 轉換時間欄位型別
        - 移除 odds_home / odds_away 為 NaN 的記錄

        Args:
            raw_records: dict 列表

        Returns:
            清洗後的 DataFrame
        """
        df = pd.DataFrame(raw_records)

        # 僅分析有效記錄
        df = df[df["is_valid"] == 1].copy()

        # 時間欄位解析
        for col in ["timestamp", "commence_time"]:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce", utc=True)

        # 確保賠率為數值型
        for col in ["odds_home", "odds_away", "odds_draw", "latency_ms"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        # 移除主/客場賠率缺失的行
        df = df.dropna(subset=["odds_home", "odds_away"])

        # 重置索引
        df = df.reset_index(drop=True)
        return df

    # ------------------------------------------------------------------
    # 穩定性分數計算
    # ------------------------------------------------------------------

    def _compute_stability_scores(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        計算每個 (match_id, platform) 組合在滾動視窗內的數據源穩定性分數。

        穩定性分數定義：
        - 計算 30 分鐘視窗內的賠率變動次數（change_count）
        - 計算賠率變動幅度的標準差（odds_std）
        - 穩定性分數 = 1 / (1 + change_count × odds_std）
          → 分數越接近 1.0 表示賠率越穩定
          → 分數越低表示賠率頻繁變動，數據源可能不可靠

        Args:
            df: 清洗後的 DataFrame（需含 timestamp, match_id, platform,
                                       odds_home, odds_away）

        Returns:
            含 match_id、platform、stability_score 的聚合 DataFrame
        """
        window_td = timedelta(minutes=self._stability_window)
        results: list[dict[str, Any]] = []

        for (match_id, platform), group in df.groupby(["match_id", "platform"]):
            group = group.sort_values("timestamp")

            if len(group) < 2:
                # 只有一筆記錄，無法計算變動，給予最高穩定分
                results.append({
                    "match_id": match_id,
                    "platform": platform,
                    "stability_score": 1.0,
                    "change_count": 0,
                    "odds_home_std": 0.0,
                    "odds_away_std": 0.0
                })
                continue

            # 計算相鄰記錄的賠率變動量（絕對值）
            group = group.copy()
            group["home_change"] = group["odds_home"].diff().abs()
            group["away_change"] = group["odds_away"].diff().abs()
            group["any_change"] = (
                (group["home_change"] > 0) | (group["away_change"] > 0)
            )

            # 在滾動時間視窗內聚合
            # 取最新時間點為視窗基準（模擬 "最近 N 分鐘" 的行為）
            latest_ts = group["timestamp"].max()
            window_start = latest_ts - pd.Timedelta(minutes=self._stability_window)
            window_group = group[group["timestamp"] >= window_start]

            change_count = int(window_group["any_change"].sum())
            odds_home_std = float(window_group["odds_home"].std(ddof=0)
                                  if len(window_group) > 1 else 0.0)
            odds_away_std = float(window_group["odds_away"].std(ddof=0)
                                  if len(window_group) > 1 else 0.0)
            avg_std = (odds_home_std + odds_away_std) / 2.0

            # 穩定性分數公式（有界於 [0, 1]）
            stability = 1.0 / (1.0 + change_count * (avg_std + 1e-9))
            stability = round(min(1.0, max(0.0, stability)), 4)

            results.append({
                "match_id": match_id,
                "platform": platform,
                "stability_score": stability,
                "change_count": change_count,
                "odds_home_std": round(odds_home_std, 6),
                "odds_away_std": round(odds_away_std, 6)
            })

        return pd.DataFrame(results)

    # ------------------------------------------------------------------
    # 異常值標記
    # ------------------------------------------------------------------

    def _flag_anomalies(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        標記賠率異常變動點。

        異常判定邏輯（透明、可追溯）：
        1. 計算每場賽事的 odds_home / odds_away 整體標準差
        2. 計算每筆記錄的賠率與均值的絕對偏差
        3. 若偏差 > N × 標準差（N = anomaly_threshold_sigma），標記為異常
        4. 記錄判定依據（anomaly_reason）避免黑盒判斷

        Args:
            df: 含穩定性分數的 DataFrame

        Returns:
            加入 anomaly_flag、anomaly_reason 欄位的 DataFrame
        """
        df = df.copy()
        df["anomaly_flag"] = False
        df["anomaly_reason"] = ""

        for match_id, group in df.groupby("match_id"):
            if len(group) < 3:
                # 樣本數不足，無法可靠計算標準差
                continue

            home_std = group["odds_home"].std(ddof=1)
            away_std = group["odds_away"].std(ddof=1)
            home_mean = group["odds_home"].mean()
            away_mean = group["odds_away"].mean()

            if pd.isna(home_std) or home_std == 0:
                home_std = 1e-9
            if pd.isna(away_std) or away_std == 0:
                away_std = 1e-9

            threshold_home = self._anomaly_sigma * home_std
            threshold_away = self._anomaly_sigma * away_std

            for idx in group.index:
                row = df.loc[idx]
                reasons: list[str] = []

                home_dev = abs(row["odds_home"] - home_mean)
                away_dev = abs(row["odds_away"] - away_mean)

                if home_dev > threshold_home:
                    reasons.append(
                        f"odds_home 偏差 {home_dev:.4f} > {self._anomaly_sigma}σ"
                        f"（σ={home_std:.4f}，均值={home_mean:.4f}）"
                    )
                if away_dev > threshold_away:
                    reasons.append(
                        f"odds_away 偏差 {away_dev:.4f} > {self._anomaly_sigma}σ"
                        f"（σ={away_std:.4f}，均值={away_mean:.4f}）"
                    )

                if reasons:
                    df.loc[idx, "anomaly_flag"] = True
                    df.loc[idx, "anomaly_reason"] = "; ".join(reasons)

        anomaly_count = df["anomaly_flag"].sum()
        logger.info("異常值標記完成：%d 筆記錄被標記為異常。", anomaly_count)
        return df

    # ------------------------------------------------------------------
    # 套利 ROI 計算
    # ------------------------------------------------------------------

    def _compute_arbitrage_roi(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        計算每場賽事跨平台的最佳隱含機率總和與 ROI。

        演算法：
        - 對每場賽事（match_id），找出各結果（home/away/draw）的最高賠率
        - 最高賠率對應最低隱含機率，總和越低 → ROI 越高
        - S = 1/best_odds_home + 1/best_odds_away [+ 1/best_odds_draw]
        - ROI = 1/S - 1
        - ROI > 0 → 理論套利機會（實際執行需考慮手續費與流動性）

        Args:
            df: 分析 DataFrame

        Returns:
            含 match_id、implied_prob_sum、roi、has_arb_opportunity 的聚合 DataFrame
        """
        arb_rows: list[dict[str, Any]] = []

        for match_id, group in df.groupby("match_id"):
            best_home = group["odds_home"].max()
            best_away = group["odds_away"].max()

            # 平局（部分運動項目才有）
            has_draw = (
                "odds_draw" in group.columns and
                group["odds_draw"].notna().any()
            )
            best_draw = group["odds_draw"].max() if has_draw else None

            # 計算隱含機率總和
            implied_sum = (1.0 / best_home) + (1.0 / best_away)
            if has_draw and best_draw and best_draw > 1.0:
                implied_sum += 1.0 / best_draw

            roi = (1.0 / implied_sum) - 1.0

            # 找出各最佳賠率對應的平台（方便稽核追溯）
            platform_home = group.loc[
                group["odds_home"].idxmax(), "platform"
            ]
            platform_away = group.loc[
                group["odds_away"].idxmax(), "platform"
            ]

            arb_rows.append({
                "match_id": match_id,
                "home_team": group["home_team"].iloc[0],
                "away_team": group["away_team"].iloc[0],
                "sport": group["sport"].iloc[0],
                "best_odds_home": round(best_home, 4),
                "best_odds_away": round(best_away, 4),
                "best_odds_draw": round(best_draw, 4) if best_draw else None,
                "platform_home": platform_home,
                "platform_away": platform_away,
                "implied_prob_sum": round(implied_sum, 6),
                "roi": round(roi, 6),
                "has_arb_opportunity": roi > self._min_roi,
                "has_draw_market": has_draw,
                "snapshot_timestamp": str(group["timestamp"].max())
            })

        arb_df = pd.DataFrame(arb_rows)
        if not arb_df.empty:
            positive_roi = (arb_df["roi"] > 0).sum()
            logger.info(
                "ROI 計算完成：%d 場賽事中，%d 場具正 ROI（最高 ROI: %.4f%%）。",
                len(arb_df), positive_roi,
                arb_df["roi"].max() * 100 if not arb_df.empty else 0
            )
        return arb_df

    # ------------------------------------------------------------------
    # 匯出介面
    # ------------------------------------------------------------------

    def export_for_powerbi(
        self,
        df: pd.DataFrame,
        filename_prefix: str = "odds_snapshot"
    ) -> str:
        """
        匯出攤平的 CSV 供 Power BI 直接匯入。

        CSV 欄位包含：
        - 所有原始快照欄位
        - anomaly_flag、anomaly_reason（異常標記）
        - stability_score、change_count（穩定性分數）
        - implied_prob_sum、roi（套利指標）

        Args:
            df:              分析完成的 DataFrame
            filename_prefix: 輸出檔案名稱前綴

        Returns:
            CSV 檔案的完整路徑字串
        """
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        csv_path = self._csv_dir / f"{filename_prefix}_{ts}.csv"

        # 選取 Power BI 需要的欄位（若欄位存在）
        desired_cols = [
            "id", "match_id", "sport", "platform",
            "home_team", "away_team",
            "odds_home", "odds_away", "odds_draw",
            "timestamp", "commence_time", "latency_ms",
            "is_valid", "invalid_reason",
            "anomaly_flag", "anomaly_reason",
            "stability_score", "change_count",
            "odds_home_std", "odds_away_std",
            "implied_prob_sum", "roi", "has_arb_opportunity"
        ]
        export_cols = [c for c in desired_cols if c in df.columns]
        export_df = df[export_cols].copy()

        # 轉換 bool → int（Power BI 相容性更好）
        for bool_col in ["anomaly_flag", "has_arb_opportunity"]:
            if bool_col in export_df.columns:
                export_df[bool_col] = export_df[bool_col].astype(int)

        export_df.to_csv(csv_path, index=False, encoding="utf-8-sig")
        logger.info("Power BI CSV 已匯出：%s（%d 列）", csv_path, len(export_df))
        return str(csv_path)

    def export_markdown_report(
        self,
        df: pd.DataFrame,
        arb_records: list[dict[str, Any]],
        top_n: int = 10
    ) -> str:
        """
        產生 Markdown 格式的分析摘要報告。

        報告內容：
        1. 執行摘要（資料量、時間範圍、異常統計）
        2. ROI 最高的前 N 組套利機會
        3. 異常數據點清單（含判定依據）

        Args:
            df:          分析完成的 DataFrame
            arb_records: 套利機會 dict 列表
            top_n:       報告顯示的最高 ROI 組合數

        Returns:
            Markdown 報告檔案路徑
        """
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        lines: list[str] = []

        lines.append("# 市場套利分析與資訊效率稽核報告")
        lines.append(f"\n**報告產生時間**：{now}\n")
        lines.append("---\n")

        # --- 執行摘要 ---
        lines.append("## 執行摘要\n")
        total = len(df)
        valid = df["is_valid"].sum() if "is_valid" in df.columns else total
        anomalies = (
            int(df["anomaly_flag"].sum())
            if "anomaly_flag" in df.columns else 0
        )
        sports = df["sport"].nunique() if "sport" in df.columns else 0
        platforms = df["platform"].nunique() if "platform" in df.columns else 0

        lines.append(f"| 指標 | 數值 |")
        lines.append(f"|------|------|")
        lines.append(f"| 總快照記錄數 | {total:,} |")
        lines.append(f"| 有效記錄數 | {valid:,} |")
        lines.append(f"| 異常標記記錄數 | {anomalies:,} |")
        lines.append(f"| 覆蓋運動項目數 | {sports} |")
        lines.append(f"| 覆蓋博彩平台數 | {platforms} |")

        if not df.empty and "timestamp" in df.columns:
            ts_min = df["timestamp"].min()
            ts_max = df["timestamp"].max()
            lines.append(f"| 數據時間範圍 | {ts_min} → {ts_max} |")

        lines.append("\n---\n")

        # --- ROI 最高的套利機會 ---
        lines.append(f"## 套利機會（前 {top_n} 組，依 ROI 排序）\n")
        arb_df = pd.DataFrame(arb_records) if arb_records else pd.DataFrame()

        if not arb_df.empty and "roi" in arb_df.columns:
            top_arb = (
                arb_df[arb_df["roi"] > self._min_roi]
                .nlargest(top_n, "roi")
            )
            if top_arb.empty:
                lines.append("*本次分析未發現正 ROI 套利機會。*\n")
            else:
                lines.append(
                    "| # | 賽事 | 主場平台/賠率 | 客場平台/賠率 "
                    "| 隱含機率總和 | ROI |"
                )
                lines.append("|---|------|---------------|---------------|---------|-----|")
                for rank, (_, row) in enumerate(top_arb.iterrows(), 1):
                    match_str = f"{row.get('home_team', '?')} vs {row.get('away_team', '?')}"
                    home_str = (
                        f"{row.get('platform_home', '?')} @ "
                        f"{row.get('best_odds_home', 0):.4f}"
                    )
                    away_str = (
                        f"{row.get('platform_away', '?')} @ "
                        f"{row.get('best_odds_away', 0):.4f}"
                    )
                    roi_pct = f"{row.get('roi', 0) * 100:.3f}%"
                    s_val = f"{row.get('implied_prob_sum', 0):.6f}"
                    lines.append(
                        f"| {rank} | {match_str} | {home_str} | "
                        f"{away_str} | {s_val} | **{roi_pct}** |"
                    )
        else:
            lines.append("*無套利計算資料可顯示。*\n")

        lines.append("\n---\n")

        # --- 異常數據點清單 ---
        lines.append("## 異常數據點清單\n")
        if "anomaly_flag" in df.columns:
            anomaly_df = df[df["anomaly_flag"] == True].copy()
            if anomaly_df.empty:
                lines.append("*本次分析未偵測到異常數據點。*\n")
            else:
                lines.append(
                    "| 賽事 ID | 平台 | 主場賠率 | 客場賠率 "
                    "| 時間戳 | 判定依據 |"
                )
                lines.append("|---------|------|---------|---------|--------|---------|")
                for _, row in anomaly_df.head(50).iterrows():
                    lines.append(
                        f"| `{row.get('match_id', '?')[:12]}...` "
                        f"| {row.get('platform', '?')} "
                        f"| {row.get('odds_home', 0):.4f} "
                        f"| {row.get('odds_away', 0):.4f} "
                        f"| {str(row.get('timestamp', ''))[:19]} "
                        f"| {row.get('anomaly_reason', '')[:80]} |"
                    )
        else:
            lines.append("*異常標記資料不可用。*\n")

        lines.append("\n---\n")
        lines.append(
            f"> **免責聲明**：本報告僅供學術研究與資訊效率稽核用途，"
            f"不構成任何投資建議，亦不包含自動交易功能。"
        )

        report = "\n".join(lines)
        self._md_path.write_text(report, encoding="utf-8")
        logger.info("Markdown 報告已輸出：%s", self._md_path)
        return str(self._md_path)

    def get_arbitrage_opportunities(
        self, df: pd.DataFrame
    ) -> list[dict[str, Any]]:
        """
        取得所有正 ROI 套利機會列表（方便 main.py 呼叫）。

        Args:
            df: 分析完成的 DataFrame

        Returns:
            套利機會 dict 列表，依 ROI 降序排列
        """
        arb_df = self._compute_arbitrage_roi(df)
        positive = arb_df[arb_df["roi"] > self._min_roi].copy()
        positive = positive.sort_values("roi", ascending=False)
        return positive.to_dict(orient="records")
