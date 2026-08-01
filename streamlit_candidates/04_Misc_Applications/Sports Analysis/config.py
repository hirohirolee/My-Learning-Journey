import streamlit as st
st.title('config.py - 自動化展示')
st.info('這是從原專案腳本自動包裝產生的互動式介面。')

"""
config.py - 集中管理所有系統設定

透過 python-dotenv 從 .env 讀取敏感設定（API Key、DB 路徑等），
確保明文金鑰不出現在程式碼中。所有可客製化參數均集中於此，
並在每個設定項旁附上說明與建議值範圍。
"""

import os
import logging
from dataclasses import dataclass, field
from pathlib import Path
from dotenv import load_dotenv

# 載入 .env 檔（若不存在則靜默忽略，依賴環境變數）
load_dotenv()


# ---------------------------------------------------------------------------
# 輔助函式
# ---------------------------------------------------------------------------

def _get_env(key: str, default: str | None = None, required: bool = False) -> str:
    """
    從環境變數讀取設定值。

    Args:
        key: 環境變數名稱
        default: 預設值（若環境變數不存在時使用）
        required: 若為 True 且環境變數不存在，則拋出 ValueError

    Returns:
        設定值字串
    """
    value = os.environ.get(key, default)
    if required and not value:
        raise ValueError(
            f"必要環境變數 '{key}' 未設定。請檢查 .env 檔案。"
        )
    return value or ""


# ---------------------------------------------------------------------------
# 設定資料類別
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ApiConfig:
    """The Odds API 連線與額度設定。"""

    # API 金鑰（從 .env 讀取，不得明文寫入程式碼）
    api_key: str = field(
        default_factory=lambda: _get_env("ODDS_API_KEY", required=True)
    )

    # The Odds API 基礎 URL
    base_url: str = "https://api.the-odds-api.com/v4"

    # 每月 API 呼叫總額度（免費方案 = 500）
    # 建議範圍：依您購買的方案調整
    monthly_quota: int = field(
        default_factory=lambda: int(_get_env("MONTHLY_QUOTA", "500"))
    )

    # 安全緩衝比例（超過此比例時發出警告並暫停）
    # 建議範圍：0.05–0.15；設太低會頻繁觸發警告，設太高會浪費額度
    quota_safety_buffer: float = field(
        default_factory=lambda: float(_get_env("QUOTA_SAFETY_BUFFER", "0.1"))
    )

    # 每次請求之間的最小等待秒數（禮貌性間隔）
    # 建議：≥ 1.0 秒；設定過低可能被視為濫用
    request_interval_seconds: float = field(
        default_factory=lambda: float(_get_env("REQUEST_INTERVAL_SECONDS", "2.0"))
    )

    # 指數退避最大重試次數（針對 429 / 5xx 錯誤）
    # 建議範圍：3–5；設太多會延誤輪詢週期
    max_retry_attempts: int = 4

    # 指數退避基礎等待秒數（實際等待 = base * 2^attempt）
    retry_backoff_base: float = 2.0

    # HTTP 請求逾時秒數
    request_timeout_seconds: int = 30

    # 預設 User-Agent（API 禮儀：識別您的應用程式）
    user_agent: str = "SportsArbitrageResearch/1.0 (Academic Research)"


@dataclass(frozen=True)
class DatabaseConfig:
    """SQLite 資料倉儲設定。"""

    # 資料庫檔案路徑
    db_path: str = field(
        default_factory=lambda: _get_env("DB_PATH", "./data/odds_warehouse.db")
    )

    # 資料完整性檢查：賠率合理下限（賠率 < 此值視為異常）
    min_valid_odds: float = 1.0

    # 資料完整性檢查：賠率合理上限（賠率 > 此值視為異常，防止數據錯誤）
    max_valid_odds: float = 10000.0


@dataclass(frozen=True)
class AnalysisConfig:
    """分析引擎設定。"""

    # 異常值標記門檻（倍數）：賠率變動超過標準差 N 倍時標記 anomaly_flag
    # 建議範圍：2.0–5.0；設太低會產生大量誤警，設太高會遺漏真實異常
    anomaly_threshold_sigma: float = field(
        default_factory=lambda: float(
            _get_env("ANOMALY_THRESHOLD_SIGMA", "3.0")
        )
    )

    # 滾動視窗大小（分鐘），用於計算數據源穩定性分數
    # 建議範圍：15–60 分鐘；視賽事頻率而定
    stability_window_minutes: int = field(
        default_factory=lambda: int(
            _get_env("STABILITY_WINDOW_MINUTES", "30")
        )
    )

    # 套利機會的最低 ROI 門檻（0.0 = 任何正 ROI 皆輸出）
    # 建議：0.0–0.02（0%–2%），過高會遺漏微型套利機會
    min_roi_threshold: float = 0.0

    # CSV 輸出目錄
    csv_output_dir: str = field(
        default_factory=lambda: _get_env("CSV_OUTPUT_DIR", "./output")
    )

    # Markdown 報告輸出路徑
    markdown_output_path: str = field(
        default_factory=lambda: _get_env(
            "MARKDOWN_OUTPUT_PATH", "./output/report.md"
        )
    )


@dataclass(frozen=True)
class PollingConfig:
    """排程與輪詢設定。"""

    # 持續輪詢模式下，每輪的間隔（秒）
    # 建議範圍：60–600 秒；設太短會快速消耗月額度
    polling_interval_seconds: float = field(
        default_factory=lambda: float(
            _get_env("POLLING_INTERVAL_SECONDS", "300")
        )
    )


@dataclass(frozen=True)
class LoggingConfig:
    """日誌系統設定。"""

    # 日誌等級（DEBUG / INFO / WARNING / ERROR / CRITICAL）
    log_level: str = field(
        default_factory=lambda: _get_env("LOG_LEVEL", "INFO")
    )

    # 日誌檔案路徑（None 表示僅輸出至 console）
    log_file_path: str = field(
        default_factory=lambda: _get_env("LOG_FILE_PATH", "./logs/system.log")
    )

    # 日誌格式
    log_format: str = (
        "%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s | %(message)s"
    )

    # 時間格式
    date_format: str = "%Y-%m-%d %H:%M:%S"


# ---------------------------------------------------------------------------
# 主設定物件（單例模式）
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AppConfig:
    """應用程式全域設定聚合（單一入口點）。"""

    api: ApiConfig = field(default_factory=ApiConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    analysis: AnalysisConfig = field(default_factory=AnalysisConfig)
    polling: PollingConfig = field(default_factory=PollingConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)


def get_config() -> AppConfig:
    """
    取得全域設定物件（工廠函式）。

    Returns:
        AppConfig 實例，包含所有子設定
    """
    return AppConfig()


def setup_logging(config: LoggingConfig) -> None:
    """
    初始化 logging 系統，設定 console + 檔案雙重輸出。

    Args:
        config: LoggingConfig 設定物件
    """
    log_level = getattr(logging, config.log_level.upper(), logging.INFO)
    formatter = logging.Formatter(
        fmt=config.log_format,
        datefmt=config.date_format
    )

    # 根 Logger 設定
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # 移除既有 handlers（避免重複輸出）
    root_logger.handlers.clear()

    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File Handler（自動建立目錄）
    if config.log_file_path:
        log_path = Path(config.log_file_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(
            log_path, encoding="utf-8", mode="a"
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    logging.info("日誌系統初始化完成，等級：%s", config.log_level)


# ====== 自動生成的測試執行區塊 ======
if __name__ == "__main__":
    st.write("---")
    st.subheader("函數測試區塊")
    if st.button("執行 get_config"):
        try:
            res = get_config() # 請視需要自行補上參數
            st.write("執行結果:", res)
        except Exception as e:
            st.error(f"執行出錯，可能需要提供參數：{e}")
    if st.button("執行 setup_logging"):
        try:
            res = setup_logging() # 請視需要自行補上參數
            st.write("執行結果:", res)
        except Exception as e:
            st.error(f"執行出錯，可能需要提供參數：{e}")
