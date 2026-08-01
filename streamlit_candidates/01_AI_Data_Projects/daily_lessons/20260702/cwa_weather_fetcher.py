import streamlit as st

"""
============================================================
台灣中央氣象署 (CWA) 天氣預報 API 串接程式
============================================================
作者  : 資深 Python 資料工程師
版本  : 1.0.0
說明  : 串接 CWA Open Data API，提取天氣預報資料並存入 SQLite 資料庫。
        支援：
          - F-C0032-001：今明 36 小時天氣預報
          - F-C0032-005：一週天氣預報（逐三天）

使用前請先：
  1. 複製 .env.example 為 .env 並填入您的 API 授權碼
  2. pip install -r requirements.txt
============================================================
"""

import os
import io
import ssl
import sqlite3
import logging
import sys
from datetime import datetime

import requests
from dotenv import load_dotenv

# ── 讀取 .env 檔案（必須在任何設定值使用前呼叫）──────────────
load_dotenv()

# ── 全域設定 ────────────────────────────────────────────────
API_BASE_URL: str = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/"
API_KEY: str | None = os.getenv("CWA_API_KEY")
DB_PATH: str = os.getenv("DB_PATH", "weather_data.db")

# 支援的 API 端點
ENDPOINT_36H: str = "F-C0032-001"   # 今明 36 小時天氣預報
ENDPOINT_WEEK: str = "F-D0047-003"  # 一週鄉鎮天氣預報（縣市彙整）

# ── 日誌設定 ─────────────────────────────────────────────────
# 強制將 stdout 設定為 UTF-8，確保 Windows 終端機（CP950）
# 也能正確輸出中文與 emoji 字元。
utf8_stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(utf8_stdout),
        logging.FileHandler("cwa_fetcher.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


# ============================================================
# Section 1：資料庫操作
# ============================================================

def get_db_connection() -> sqlite3.Connection:
    """
    建立並回傳 SQLite 資料庫連線。
    使用 row_factory 讓查詢結果可以用欄位名稱存取（類似 dict）。
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database(conn: sqlite3.Connection) -> None:
    """
    初始化資料庫，若資料表不存在則自動建立。

    資料表設計：
      - weather_36h  → 今明 36 小時預報
      - weather_week → 一週天氣預報

    使用 CREATE TABLE IF NOT EXISTS 確保冪等性（重複執行不會報錯）。
    """
    cursor = conn.cursor()

    # 今明 36 小時預報資料表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS weather_36h (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            location_name    TEXT    NOT NULL,          -- 縣市名稱
            start_time       TEXT    NOT NULL,          -- 預報起始時間
            end_time         TEXT    NOT NULL,          -- 預報結束時間
            weather_desc     TEXT,                      -- 天氣現象 (Wx) 描述
            weather_code     TEXT,                      -- 天氣現象代碼
            pop              INTEGER,                   -- 降雨機率 (%)
            min_temperature  INTEGER,                   -- 最低溫度 (°C)
            max_temperature  INTEGER,                   -- 最高溫度 (°C)
            fetched_at       TEXT    NOT NULL           -- 資料抓取時間
        )
    """)

    # 一週天氣預報資料表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS weather_week (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            location_name    TEXT    NOT NULL,          -- 縣市名稱
            start_time       TEXT    NOT NULL,          -- 預報起始時間
            end_time         TEXT    NOT NULL,          -- 預報結束時間
            weather_desc     TEXT,                      -- 天氣現象描述
            weather_code     TEXT,                      -- 天氣現象代碼
            pop              INTEGER,                   -- 降雨機率 (%)
            min_temperature  INTEGER,                   -- 最低溫度 (°C)
            max_temperature  INTEGER,                   -- 最高溫度 (°C)
            fetched_at       TEXT    NOT NULL           -- 資料抓取時間
        )
    """)

    conn.commit()
    logger.info("✅ 資料庫初始化完成，資料表已就緒。")


def insert_weather_records(
    conn: sqlite3.Connection,
    table_name: str,
    records: list[dict],
) -> int:
    """
    將天氣預報記錄批次 INSERT 至指定資料表。

    Args:
        conn       : SQLite 連線物件
        table_name : 目標資料表名稱 ("weather_36h" 或 "weather_week")
        records    : 欲插入的資料列表，每個元素為一筆記錄的 dict

    Returns:
        成功插入的筆數
    """
    if not records:
        logger.warning(f"⚠️  [{table_name}] 無資料可插入。")
        return 0

    sql = f"""
        INSERT INTO {table_name} (
            location_name, start_time, end_time,
            weather_desc, weather_code, pop,
            min_temperature, max_temperature, fetched_at
        ) VALUES (
            :location_name, :start_time, :end_time,
            :weather_desc, :weather_code, :pop,
            :min_temperature, :max_temperature, :fetched_at
        )
    """

    cursor = conn.cursor()
    cursor.executemany(sql, records)
    conn.commit()

    inserted_count = cursor.rowcount
    logger.info(f"✅ [{table_name}] 成功插入 {inserted_count} 筆資料。")
    return inserted_count


# ============================================================
# Section 2：API 請求
# ============================================================

def fetch_cwa_api(endpoint: str, extra_params: dict | None = None) -> dict | None:
    """
    向 CWA Open Data API 發送 GET 請求並回傳解析後的 JSON 資料。

    Args:
        endpoint     : API 端點代碼，例如 "F-C0032-001"
        extra_params : 額外的查詢參數（字典格式），會與預設參數合併

    Returns:
        成功時回傳 dict（JSON 資料），失敗時回傳 None
    """
    if not API_KEY:
        logger.error(
            "❌ 找不到 API 授權碼！請確認 .env 檔案已設定 CWA_API_KEY。"
        )
        return None

    url = f"{API_BASE_URL}{endpoint}"

    # 基礎請求參數
    params = {
        "Authorization": API_KEY,
        "format": "JSON",
    }
    if extra_params:
        params.update(extra_params)

    logger.info(f"🌐 正在請求 API：{url}")

    # ── SSL 設定 ──────────────────────────────────────────────
    # CWA 伺服器的 SSL 憑證缺少 Subject Key Identifier (SKI)，
    # 在 Python 3.12+ 的嚴格驗證下會被拒絕。
    # 使用自訂 SSLContext 繞過此憑證相容性問題。
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    # 將自訂 SSLContext 掛載至 requests 的 HTTPAdapter
    adapter = requests.adapters.HTTPAdapter()
    session = requests.Session()
    session.mount("https://", adapter)

    try:
        response = session.get(
            url,
            params=params,
            timeout=30,
            verify=False,   # 對應上方 CERT_NONE，停用憑證鏈驗證
        )

        # 若 HTTP 狀態碼為 4xx/5xx，則主動拋出例外
        response.raise_for_status()

        data = response.json()

        # 檢查 CWA API 自訂的回傳狀態欄位
        if data.get("success") != "true":
            logger.error(f"❌ API 回傳失敗狀態：{data.get('result', {})}")
            return None

        logger.info("✅ API 請求成功。")
        return data

    except requests.exceptions.SSLError as e:
        logger.error(f"❌ SSL 憑證錯誤（即使已設定略過，仍發生問題）：{e}")
    except requests.exceptions.ConnectionError:
        logger.error("❌ 網路連線失敗，請確認可連上 opendata.cwa.gov.tw。")
    except requests.exceptions.Timeout:
        logger.error(f"❌ 請求逾時（已等待 30 秒），端點：{endpoint}")
    except requests.exceptions.HTTPError as e:
        logger.error(f"❌ HTTP 錯誤：{e.response.status_code} - {e}")
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ 請求發生未知錯誤：{e}")
    except ValueError as e:
        logger.error(f"❌ JSON 解析失敗：{e}")

    return None


# ============================================================
# Section 3：資料解析（今明 36 小時）
# ============================================================

def _get_element_value(time_element: dict, element_name: str) -> str | None:
    """
    從單一時間區間的 weatherElement 列表中，依元素名稱取得值。
    這是一個內部輔助函式，簡化重複的查找邏輯。

    Args:
        time_element  : 單一時間區間的資料物件（含多個 weatherElement）
        element_name  : 要查找的天氣要素名稱（如 "Wx", "PoP", "MinT", "MaxT"）

    Returns:
        找到時回傳對應的值字串，否則回傳 None
    """
    for element in time_element.get("weatherElement", []):
        if element.get("elementName") == element_name:
            # 36 小時預報的值存放在 time[0].parameter 中
            times = element.get("time", [])
            if times:
                return times[0].get("parameter", {})
    return None


def parse_36h_forecast(raw_data: dict) -> list[dict]:
    """
    解析今明 36 小時天氣預報（F-C0032-001）的原始 JSON 資料。

    資料結構路徑：
      raw_data
        └─ records
             └─ location[] (每個縣市)
                  └─ weatherElement[] (天氣要素)
                       └─ time[] (時間區間)

    Args:
        raw_data : fetch_cwa_api() 回傳的完整 JSON dict

    Returns:
        整理後可直接 INSERT 至 weather_36h 資料表的 list[dict]
    """
    records = []
    fetched_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        locations = raw_data["records"]["location"]
    except (KeyError, TypeError):
        logger.error("❌ 36 小時預報：JSON 結構異常，找不到 location 資料。")
        return records

    for location in locations:
        location_name = location.get("locationName", "未知")

        # 建立天氣要素的快速查找索引 {elementName: element_obj}
        element_index = {
            elem["elementName"]: elem
            for elem in location.get("weatherElement", [])
        }

        # 從「天氣現象 Wx」的時間區間數量決定迴圈次數
        wx_element = element_index.get("Wx", {})
        time_slots = wx_element.get("time", [])

        for i, time_slot in enumerate(time_slots):
            start_time = time_slot.get("startTime", "")
            end_time = time_slot.get("endTime", "")

            # 取得各天氣要素在同一時間區間（索引 i）的值
            def get_param(elem_name: str, key: str = "parameterName") -> str | None:
                """從要素索引取得指定時間段的參數值"""
                elem = element_index.get(elem_name, {})
                slot = elem.get("time", [])[i] if i < len(elem.get("time", [])) else {}
                return slot.get("parameter", {}).get(key)

            record = {
                "location_name"  : location_name,
                "start_time"     : start_time,
                "end_time"       : end_time,
                "weather_desc"   : get_param("Wx", "parameterName"),
                "weather_code"   : get_param("Wx", "parameterValue"),
                "pop"            : _safe_int(get_param("PoP")),
                "min_temperature": _safe_int(get_param("MinT")),
                "max_temperature": _safe_int(get_param("MaxT")),
                "fetched_at"     : fetched_at,
            }
            records.append(record)

        logger.info(f"  📍 {location_name}：解析 {len(time_slots)} 個時間區間")

    logger.info(f"✅ 36 小時預報解析完成，共 {len(records)} 筆記錄。")
    return records


# ============================================================
# Section 4：資料解析（一週天氣預報）
# ============================================================

def parse_week_forecast(raw_data: dict) -> list[dict]:
    """
    解析一週天氣預報（F-D0047-003）的原始 JSON 資料。

    F-D0047-003 的 JSON 結構（與 F-C0032-001 完全不同）：
      raw_data
        └─ records
             └─ Locations[] (大寫，將全台测站包套)
                  └─ Location[] (小寫，每個縣市)
                       └─ WeatherElement[] (天氣要素)
                            └─ Time[] (時間區間)
                                 └─ ElementValue[] (各要素的字典，鍵名不同)

    天氣要素 ElementName（小寫）與對應的 ElementValue 鍵名：
      - '天氣現象'     → Weather / WeatherCode
      - '12小時降雨機率' → ProbabilityOfPrecipitation
      - '最高溫度'     → MaxTemperature
      - '最低溫度'     → MinTemperature

    Args:
        raw_data : fetch_cwa_api() 回傳的完整 JSON dict

    Returns:
        整理後可直接 INSERT 至 weather_week 資料表的 list[dict]
    """
    records = []
    fetched_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        # F-D0047-003 使用大寫 'Locations' 作為最外層
        locations_groups = raw_data["records"]["Locations"]
    except (KeyError, TypeError):
        logger.error("❌ 一週預報：JSON 結構異常，找不到 Locations 資料。")
        return records

    for locations_group in locations_groups:
        # 每個 Locations 包含多個 Location（小寫）
        for location in locations_group.get("Location", []):
            location_name = location.get("LocationName", "未知")

            # 建立天氣要素的快速查找索引 {ElementName: element_obj}
            element_index = {
                elem.get("ElementName", ""): elem
                for elem in location.get("WeatherElement", [])
            }

            # 取得天氣現象的時間區間數量來決定迴圈次數
            wx_element = element_index.get("天氣現象", {})
            time_slots = wx_element.get("Time", [])

            for i, time_slot in enumerate(time_slots):
                start_time = time_slot.get("StartTime", "")
                end_time   = time_slot.get("EndTime", "")

                def get_ev(elem_name: str, value_key: str, idx: int = i) -> str | None:
                    """
                    從要素索引取得指定時間段的 ElementValue 元素。
                    F-D0047-003 的對應值存在 ElementValue 陣列內（字典格式）。
                    """
                    elem = element_index.get(elem_name, {})
                    times = elem.get("Time", [])
                    if idx >= len(times):
                        return None
                    ev_list = times[idx].get("ElementValue", [])
                    # ElementValue 是一個列表，第一個元素為包含複數 key 的字典
                    return ev_list[0].get(value_key) if ev_list else None

                record = {
                    "location_name"  : location_name,
                    "start_time"     : start_time,
                    "end_time"       : end_time,
                    "weather_desc"   : get_ev("天氣現象", "Weather"),
                    "weather_code"   : get_ev("天氣現象", "WeatherCode"),
                    "pop"            : _safe_int(get_ev("12小時降雨機率", "ProbabilityOfPrecipitation")),
                    "min_temperature": _safe_int(get_ev("最低溫度", "MinTemperature")),
                    "max_temperature": _safe_int(get_ev("最高溫度", "MaxTemperature")),
                    "fetched_at"     : fetched_at,
                }
                records.append(record)

            logger.info(f"  📍 {location_name}：解析 {len(time_slots)} 個時間區間")

    logger.info(f"✅ 一週預報解析完成，共 {len(records)} 筆記錄。")
    return records


# ============================================================
# Section 5：工具函式
# ============================================================

def _safe_int(value: str | None) -> int | None:
    """
    安全地將字串轉換為整數，避免 ValueError。
    若輸入為 None 或無法轉換，則回傳 None。
    """
    if value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def display_summary(conn: sqlite3.Connection) -> None:
    """
    查詢並顯示資料庫中各資料表的最新統計資訊，作為執行後的確認摘要。
    使用 sys.stdout.buffer 寫入 UTF-8 bytes，解決 Windows 終端機 CP950 無法輸出 emoji 的問題。
    """
    cursor = conn.cursor()
    tables = [
        ("weather_36h", "今明 36 小時預報"),
        ("weather_week", "一週天氣預報"),
    ]

    def uprint(text: str) -> None:
        """UTF-8 安全輸出，由 utf8_stdout 處理。"""
        st.write(text, file=utf8_stdout, flush=True)

    uprint("\n" + "=" * 60)
    uprint("  📊 資料庫儲存摘要")
    uprint("=" * 60)

    for table, label in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        total = cursor.fetchone()[0]

        cursor.execute(f"SELECT MAX(fetched_at) FROM {table}")
        latest = cursor.fetchone()[0]

        uprint(f"  [{label}]")
        uprint(f"    資料表   : {table}")
        uprint(f"    總筆數   : {total} 筆")
        uprint(f"    最新抓取 : {latest or 'N/A'}")
        uprint("")

    uprint("=" * 60)


# ============================================================
# Section 6：主程式進入點
# ============================================================

def main() -> None:
    """
    主流程協調函式：
      1. 驗證 API 授權碼
      2. 初始化資料庫
      3. 抓取今明 36 小時預報 → 解析 → 儲存
      4. 抓取一週天氣預報   → 解析 → 儲存
      5. 顯示摘要
    """
    logger.info("🚀 CWA 天氣資料抓取程式啟動")
    logger.info(f"   資料庫路徑：{DB_PATH}")

    # ── 步驟 0：驗證授權碼 ────────────────────────────────
    if not API_KEY or API_KEY == "YOUR_API_KEY_HERE":
        logger.error(
            "❌ 請先設定 .env 檔案中的 CWA_API_KEY！\n"
            "   參考 .env.example 建立您的 .env 檔案。"
        )
        sys.exit(1)

    # ── 步驟 1：建立資料庫連線並初始化 ───────────────────
    conn = get_db_connection()
    try:
        initialize_database(conn)

        # ── 步驟 2：今明 36 小時預報 ─────────────────────
        logger.info("\n── 開始處理：今明 36 小時天氣預報 ──")
        raw_36h = fetch_cwa_api(ENDPOINT_36H)
        if raw_36h:
            records_36h = parse_36h_forecast(raw_36h)
            insert_weather_records(conn, "weather_36h", records_36h)
        else:
            logger.warning("⚠️  36 小時預報資料取得失敗，跳過此步驟。")

        # ── 步驟 3：一週天氣預報 ─────────────────────────
        logger.info("\n── 開始處理：一週天氣預報 ──")
        raw_week = fetch_cwa_api(ENDPOINT_WEEK)
        if raw_week:
            records_week = parse_week_forecast(raw_week)
            insert_weather_records(conn, "weather_week", records_week)
        else:
            logger.warning("⚠️  一週預報資料取得失敗，跳過此步驟。")

        # ── 步驟 4：顯示執行摘要 ─────────────────────────
        display_summary(conn)
        logger.info("🏁 程式執行完成。")

    except sqlite3.DatabaseError as e:
        logger.error(f"❌ 資料庫操作失敗：{e}")
        sys.exit(1)
    finally:
        # 確保無論如何都會關閉資料庫連線，避免資源洩漏
        conn.close()
        logger.info("🔒 資料庫連線已關閉。")


if __name__ == "__main__":
    main()
