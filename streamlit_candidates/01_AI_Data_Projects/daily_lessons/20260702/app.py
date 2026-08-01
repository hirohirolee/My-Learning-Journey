# ============================================================
# 台灣天氣即時監測儀表板 - Streamlit App
# ============================================================
# NCHU AI 課程實作專案 ｜ 版本 2.0
#
# 需要安裝的套件：
#   pip install streamlit pandas plotly folium streamlit-folium
#
# 執行方式：
#   streamlit run app.py
#
# 架構說明：
#   本程式採用模組化設計，各功能區塊分離為獨立函式，
#   便於後續擴充與維護。主程式 main() 僅負責協調呼叫順序。
#
# 版面佈局（由上至下）：
#   1. 標題列 & KPI 卡片
#   2. 全台天氣地圖（Folium / OpenStreetMap）
#   3. 氣象預測圖表（Plotly 折線圖 + 長條圖）
#   4. 頁尾
# ============================================================

import sqlite3
import os
import ssl
import json
from datetime import datetime

import requests
import pandas as pd
import plotly.graph_objects as go
import folium
import streamlit as st
from streamlit_folium import st_folium


# ============================================================
# Section 0：全域常數
# ============================================================

# 資料庫路徑
# On Streamlit Cloud, /tmp is writable and persists within a session.
# Locally we use the script directory.
_IS_CLOUD = "STREAMLIT_SHARING_MODE" in os.environ or os.environ.get("HOME", "") == "/home/appuser"
DB_PATH: str = (
    "/tmp/weather_data.db"
    if _IS_CLOUD
    else os.path.join(os.path.dirname(os.path.abspath(__file__)), "weather_data.db")
)

CWA_API_BASE: str = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/"
ENDPOINT_36H: str = "F-C0032-001"

# 台灣各縣市中心座標 (lat, lon)
LOCATION_COORDS: dict[str, tuple[float, float]] = {
    "臺北市": (25.0330, 121.5654),
    "新北市": (25.0170, 121.4627),
    "基隆市": (25.1276, 121.7392),
    "桃園市": (24.9936, 121.3010),
    "新竹市": (24.8138, 120.9675),
    "新竹縣": (24.7036, 121.1542),
    "苗栗縣": (24.5600, 120.8214),
    "臺中市": (24.1477, 120.6736),
    "彰化縣": (24.0518, 120.5161),
    "南投縣": (23.9610, 120.9720),
    "雲林縣": (23.7092, 120.4313),
    "嘉義市": (23.4801, 120.4491),
    "嘉義縣": (23.4518, 120.2554),
    "臺南市": (22.9998, 120.2269),
    "高雄市": (22.6273, 120.3014),
    "屏東縣": (22.5519, 120.5487),
    "宜蘭縣": (24.7021, 121.7378),
    "花蓮縣": (23.9871, 121.6015),
    "臺東縣": (22.7583, 121.1444),
    "澎湖縣": (23.5711, 119.5793),
    "金門縣": (24.4493, 118.3767),
    "連江縣": (26.1506, 119.9289),
}

# 天氣現象文字 → emoji 對照表
WEATHER_EMOJI: dict[str, str] = {
    "晴":   "☀️",
    "多雲": "⛅",
    "陰":   "☁️",
    "雨":   "🌧️",
    "雷":   "⛈️",
    "霧":   "🌫️",
    "雪":   "❄️",
}

# 降雨機率 → Folium Marker 顏色（確保在彩色底圖上高辨識度）
# 使用 folium.Icon 支援的標準顏色名稱
POP_MARKER_COLOR: list[tuple[int, str]] = [
    (30,  "green"),   # 低雨機率：綠色
    (60,  "orange"),  # 中雨機率：橘色
    (100, "red"),     # 高雨機率：紅色
]


# ============================================================
# Section 1：資料層 (Data Layer)
# ============================================================

# ============================================================
# Section 1b：自動抓取 (Auto-Fetch for Streamlit Cloud)
# ============================================================

def _cwa_fetch_and_seed_db() -> bool:
    """
    When running on Streamlit Cloud (no local DB), automatically fetch
    live 36-hour forecast data from CWA API and seed the SQLite DB.
    Requires CWA_API_KEY to be set in st.secrets or environment.
    Returns True on success, False on failure.
    """
    # ── Resolve API Key ──────────────────────────────────────
    api_key = os.environ.get("CWA_API_KEY", "")
    if not api_key:
        try:
            api_key = st.secrets.get("CWA_API_KEY", "")
        except Exception:
            pass
    if not api_key:
        return False

    # ── Fetch from CWA API ───────────────────────────────────
    url = f"{CWA_API_BASE}{ENDPOINT_36H}"
    params = {"Authorization": api_key, "format": "JSON"}
    try:
        resp = requests.get(url, params=params, timeout=30, verify=False)
        resp.raise_for_status()
        data = resp.json()
        if data.get("success") != "true":
            return False
    except Exception:
        return False

    # ── Parse Records ────────────────────────────────────────
    records = []
    fetched_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        locations = data["records"]["location"]
    except (KeyError, TypeError):
        return False

    for location in locations:
        location_name = location.get("locationName", "未知")
        element_index = {
            elem["elementName"]: elem
            for elem in location.get("weatherElement", [])
        }
        wx_element = element_index.get("Wx", {})
        time_slots = wx_element.get("time", [])

        for i, time_slot in enumerate(time_slots):
            def get_param(elem_name, key="parameterName", _i=i):
                elem = element_index.get(elem_name, {})
                slot = elem.get("time", [])[_i] if _i < len(elem.get("time", [])) else {}
                return slot.get("parameter", {}).get(key)

            def safe_int(v):
                try:
                    return int(v) if v is not None else None
                except (ValueError, TypeError):
                    return None

            records.append({
                "location_name"  : location_name,
                "start_time"     : time_slot.get("startTime", ""),
                "end_time"       : time_slot.get("endTime", ""),
                "weather_desc"   : get_param("Wx", "parameterName"),
                "weather_code"   : get_param("Wx", "parameterValue"),
                "pop"            : safe_int(get_param("PoP")),
                "min_temperature": safe_int(get_param("MinT")),
                "max_temperature": safe_int(get_param("MaxT")),
                "fetched_at"     : fetched_at,
            })

    if not records:
        return False

    # ── Seed SQLite ──────────────────────────────────────────
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS weather_36h (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                location_name TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                weather_desc TEXT,
                weather_code TEXT,
                pop INTEGER,
                min_temperature INTEGER,
                max_temperature INTEGER,
                fetched_at TEXT NOT NULL
            )
        """)
        conn.executemany("""
            INSERT INTO weather_36h
            (location_name, start_time, end_time, weather_desc, weather_code,
             pop, min_temperature, max_temperature, fetched_at)
            VALUES
            (:location_name, :start_time, :end_time, :weather_desc, :weather_code,
             :pop, :min_temperature, :max_temperature, :fetched_at)
        """, records)
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False


def _seed_sample_weather_data() -> bool:
    import random
    locations = list(LOCATION_COORDS.keys())
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    start_str = datetime.now().strftime("%Y-%m-%d 06:00:00")
    end_str = datetime.now().strftime("%Y-%m-%d 18:00:00")
    
    sample_records = []
    weather_options = [
        ("多雲短暫陣雨", "20", 30, 26, 32),
        ("晴時多雲", "01", 10, 27, 34),
        ("陰局部雨", "08", 60, 24, 29),
        ("多雲", "03", 20, 26, 33),
        ("晴朗", "01", 0, 28, 35)
    ]
    for loc in locations:
        desc, code, pop, mint, maxt = random.choice(weather_options)
        sample_records.append({
            "location_name": loc,
            "start_time": start_str,
            "end_time": end_str,
            "weather_desc": desc,
            "weather_code": code,
            "pop": pop,
            "min_temperature": mint,
            "max_temperature": maxt,
            "fetched_at": now_str
        })
    try:
        os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS weather_36h (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                location_name TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                weather_desc TEXT,
                weather_code TEXT,
                pop INTEGER,
                min_temperature INTEGER,
                max_temperature INTEGER,
                fetched_at TEXT NOT NULL
            )
        """)
        conn.executemany("""
            INSERT INTO weather_36h
            (location_name, start_time, end_time, weather_desc, weather_code,
             pop, min_temperature, max_temperature, fetched_at)
            VALUES
            (:location_name, :start_time, :end_time, :weather_desc, :weather_code,
             :pop, :min_temperature, :max_temperature, :fetched_at)
        """, sample_records)
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False


@st.cache_data(ttl=300)  # 快取 5 分鐘，避免重複 I/O
def load_data() -> pd.DataFrame | None:
    if not os.path.exists(DB_PATH):
        with st.spinner("⏳ 正在讀取氣象數據..."):
            success = _cwa_fetch_and_seed_db()
            if not success:
                _seed_sample_weather_data()

    # ── 讀取資料 ──────────────────────────────────────────────
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query(
            "SELECT * FROM weather_36h ORDER BY location_name, start_time",
            conn,
        )
        conn.close()
    except Exception as exc:
        st.error(f"❌ 資料庫讀取失敗：{exc}")
        return None

    # ── 防呆：空資料表 ─────────────────────────────────────────
    if df.empty:
        st.warning("⚠️ 資料庫尚無資料，請先執行爬蟲程式抓取資料。")
        return None

    # ── 數值型態轉換（coerce 使無效值轉為 NaN，不崩潰）─────────
    for col in ("pop", "min_temperature", "max_temperature"):
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # ── 時間欄位轉換 ──────────────────────────────────────────
    df["start_time"] = pd.to_datetime(df["start_time"], errors="coerce")
    df["end_time"]   = pd.to_datetime(df["end_time"],   errors="coerce")

    # ── 圖表用的 X 軸標籤 ────────────────────────────────────
    df["time_label"] = df["start_time"].dt.strftime("%m/%d %H:%M")

    return df


def get_latest_per_city(df: pd.DataFrame) -> pd.DataFrame:
    """
    從完整 DataFrame 中取出各縣市「最新批次、最早時段」的一筆記錄，
    供地圖 Marker 使用。

    Args:
        df : 完整天氣 DataFrame

    Returns:
        每縣市各一列的 DataFrame
    """
    return (
        df.sort_values(["fetched_at", "start_time"], ascending=[False, True])
          .groupby("location_name", as_index=False)
          .first()
    )


# ============================================================
# Section 2：工具函式 (Utility Layer)
# ============================================================

def get_weather_emoji(desc: str | None) -> str:
    """根據天氣描述字串回傳對應 emoji，無法匹配時回傳 🌡️。"""
    if not desc:
        return "🌡️"
    for keyword, emoji in WEATHER_EMOJI.items():
        if keyword in desc:
            return emoji
    return "🌡️"


def get_pop_marker_color(pop_val: float | None) -> str:
    """
    依降雨機率回傳 Folium Icon 顏色名稱。
    顏色在彩色 OpenStreetMap 底圖上具備高辨識度。

    Args:
        pop_val : 降雨機率數值（0-100），None 視為 0

    Returns:
        folium.Icon 支援的顏色字串
    """
    val = pop_val if pop_val is not None else 0
    for threshold, color in POP_MARKER_COLOR:
        if val <= threshold:
            return color
    return "red"


def build_popup_html(city: str, desc: str, maxt: str, mint: str, pop: str, emoji: str) -> str:
    """
    產生 Folium Popup 的 HTML 內容（白底卡片，適合彩色底圖）。

    Args:
        city  : 縣市名稱
        desc  : 天氣現象描述
        maxt  : 最高溫字串
        mint  : 最低溫字串
        pop   : 降雨機率字串
        emoji : 天氣 emoji

    Returns:
        HTML 字串
    """
    return f"""
    <div style="
        font-family: 'Noto Sans TC', 'Microsoft JhengHei', sans-serif;
        background: #FFFFFF;
        color: #212121;
        padding: 14px 18px;
        border-radius: 12px;
        border-left: 5px solid #1976D2;
        min-width: 180px;
        font-size: 13px;
        box-shadow: 0 4px 16px rgba(0,0,0,0.18);
        line-height: 1.7;
    ">
        <div style="font-size:17px; font-weight:700; color:#1565C0; margin-bottom:6px;">
            {emoji} {city}
        </div>
        <div style="color:#455A64; margin-bottom:8px; font-size:12px;">
            ☁️&nbsp;{desc}
        </div>
        <table style="width:100%; border-collapse:collapse; font-size:12.5px;">
            <tr>
                <td>🌡️ 高溫</td>
                <td style="text-align:right; font-weight:700; color:#D32F2F;">{maxt}</td>
            </tr>
            <tr>
                <td>❄️ 低溫</td>
                <td style="text-align:right; font-weight:700; color:#0288D1;">{mint}</td>
            </tr>
            <tr>
                <td>🌧️ 降雨機率</td>
                <td style="text-align:right; font-weight:700; color:#1976D2;">{pop}</td>
            </tr>
        </table>
    </div>
    """


# ============================================================
# Section 3：地圖區塊 (Map Section)
# ============================================================

def build_taiwan_map(df: pd.DataFrame) -> folium.Map:
    """
    建立彩色 OpenStreetMap 底圖，並在各縣市加入 Marker。

    設計原則：
      - tiles="OpenStreetMap" 確保呈現豐富彩色地圖
      - 使用 folium.Marker + DivIcon 取代 CircleMarker，
        讓圖示在彩色底圖上擁有高辨識度（白框 + 彩色背景）

    Args:
        df : 完整天氣 DataFrame

    Returns:
        配置好 Marker 的 folium.Map 物件
    """
    # ── 初始化地圖（OpenStreetMap 彩色底圖）──────────────────
    taiwan_map = folium.Map(
        location=[23.6978, 120.9605],   # 台灣幾何中心
        zoom_start=7,
        tiles="OpenStreetMap",          # 強制彩色底圖，禁用灰階
    )

    # ── 取各縣市最新一筆資料 ──────────────────────────────────
    latest = get_latest_per_city(df)

    for _, row in latest.iterrows():
        city   = row["location_name"]
        coords = LOCATION_COORDS.get(city)
        if coords is None:
            continue  # 未設定座標的縣市略過

        # 準備顯示值
        emoji = get_weather_emoji(row.get("weather_desc"))
        desc  = row.get("weather_desc") or "未知"
        pop_v = row.get("pop")
        mint_v = row.get("min_temperature")
        maxt_v = row.get("max_temperature")

        pop  = f"{pop_v:.0f}%"   if pd.notna(pop_v)  else "N/A"
        mint = f"{mint_v:.0f}°C" if pd.notna(mint_v) else "N/A"
        maxt = f"{maxt_v:.0f}°C" if pd.notna(maxt_v) else "N/A"

        # ── Marker 顏色（依降雨機率，確保彩色底圖高辨識度）──
        icon_color = get_pop_marker_color(pop_v)

        # ── 自訂 DivIcon：圓形標籤含縣市縮寫，視覺清晰 ─────
        city_abbr = city[:2]   # 取前兩字作為圖示標籤（如「臺北」）
        icon_html = f"""
        <div style="
            background-color: {'#E53935' if icon_color == 'red' else '#FB8C00' if icon_color == 'orange' else '#43A047'};
            color: white;
            border: 2px solid white;
            border-radius: 50%;
            width: 34px;
            height: 34px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 10px;
            font-weight: 700;
            font-family: 'Microsoft JhengHei', sans-serif;
            box-shadow: 0 2px 6px rgba(0,0,0,0.35);
            cursor: pointer;
        ">{city_abbr}</div>
        """

        folium.Marker(
            location=coords,
            icon=folium.DivIcon(
                html=icon_html,
                icon_size=(34, 34),
                icon_anchor=(17, 17),  # 圓心對齊座標點
            ),
            popup=folium.Popup(
                build_popup_html(city, desc, maxt, mint, pop, emoji),
                max_width=230,
            ),
            tooltip=f"{emoji} {city}｜{maxt}/{mint}｜雨 {pop}",
        ).add_to(taiwan_map)

    return taiwan_map


def render_map_section(df: pd.DataFrame) -> None:
    """
    渲染地圖區塊（儀表板上半部）。
    包含區塊標題、說明文字與 Folium 地圖。

    Args:
        df : 完整天氣 DataFrame
    """
    st.markdown("### 🗺️ 全台天氣地圖")
    st.caption("🟢 低雨機率　🟠 中雨機率　🔴 高雨機率｜點擊縣市標記查看詳細天氣資訊")

    taiwan_map = build_taiwan_map(df)

    # 使用 streamlit_folium 渲染地圖至畫面
    st_folium(
        taiwan_map,
        use_container_width=True,
        height=520,
        returned_objects=[],  # 不需要監聽點擊事件回傳
    )


# ============================================================
# Section 4：圖表區塊 (Charts Section)
# ============================================================

def build_temperature_chart(df_city: pd.DataFrame, city: str) -> go.Figure:
    """
    建立最高溫與最低溫的雙線折線圖（含填色區域）。

    Args:
        df_city : 已篩選為單一縣市的 DataFrame
        city    : 縣市名稱（用於標題）

    Returns:
        Plotly Figure 物件
    """
    fig = go.Figure()

    # ── 最高溫折線（珊瑚紅）────────────────────────────────
    fig.add_trace(go.Scatter(
        x=df_city["time_label"],
        y=df_city["max_temperature"],
        mode="lines+markers+text",
        name="最高溫 (°C)",
        line=dict(color="#FF6B6B", width=3),
        marker=dict(size=9, color="#FF6B6B", line=dict(color="white", width=1.5)),
        text=df_city["max_temperature"].apply(
            lambda v: f"{v:.0f}°" if pd.notna(v) else ""
        ),
        textposition="top center",
        textfont=dict(size=11, color="#FF6B6B", family="Noto Sans TC"),
        hovertemplate="<b>最高溫</b>: %{y}°C<br>時間: %{x}<extra></extra>",
    ))

    # ── 最低溫折線（青藍色），填滿兩線之間 ──────────────────
    fig.add_trace(go.Scatter(
        x=df_city["time_label"],
        y=df_city["min_temperature"],
        mode="lines+markers+text",
        name="最低溫 (°C)",
        line=dict(color="#4ECDC4", width=3),
        marker=dict(size=9, color="#4ECDC4", line=dict(color="white", width=1.5)),
        text=df_city["min_temperature"].apply(
            lambda v: f"{v:.0f}°" if pd.notna(v) else ""
        ),
        textposition="bottom center",
        textfont=dict(size=11, color="#4ECDC4", family="Noto Sans TC"),
        hovertemplate="<b>最低溫</b>: %{y}°C<br>時間: %{x}<extra></extra>",
        fill="tonexty",
        fillcolor="rgba(78, 205, 196, 0.1)",
    ))

    fig.update_layout(
        title=dict(text=f"🌡️ {city} — 氣溫預測趨勢", font=dict(size=17, color="#E8EAF6"), x=0.5),
        paper_bgcolor="#1A1A2E",
        plot_bgcolor="#1A1A2E",
        font=dict(color="#B0BEC5", family="Noto Sans TC"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, bgcolor="rgba(0,0,0,0)"),
        xaxis=dict(title="預測時段", gridcolor="#2D2D4E", linecolor="#444", showline=True),
        yaxis=dict(title="溫度 (°C)", gridcolor="#2D2D4E", linecolor="#444", showline=True),
        hovermode="x unified",
        margin=dict(l=40, r=20, t=60, b=40),
    )
    return fig


def build_pop_chart(df_city: pd.DataFrame, city: str) -> go.Figure:
    """
    建立降雨機率長條圖，顏色依數值深淺動態變化。

    Args:
        df_city : 已篩選為單一縣市的 DataFrame
        city    : 縣市名稱（用於標題）

    Returns:
        Plotly Figure 物件
    """
    # 依降雨機率計算每根柱子的透明度（機率越高越深）
    bar_colors = [
        f"rgba(29, 145, 192, {0.35 + (v / 100) * 0.65})"
        if pd.notna(v) else "rgba(100,100,100,0.4)"
        for v in df_city["pop"]
    ]

    fig = go.Figure(go.Bar(
        x=df_city["time_label"],
        y=df_city["pop"],
        marker=dict(color=bar_colors, line=dict(width=0)),
        text=df_city["pop"].apply(lambda v: f"{v:.0f}%" if pd.notna(v) else "N/A"),
        textposition="outside",
        textfont=dict(size=11, color="#90CAF9", family="Noto Sans TC"),
        hovertemplate="<b>降雨機率</b>: %{y}%<br>時間: %{x}<extra></extra>",
    ))

    fig.update_layout(
        title=dict(text=f"🌧️ {city} — 降雨機率預測", font=dict(size=17, color="#E8EAF6"), x=0.5),
        paper_bgcolor="#1A1A2E",
        plot_bgcolor="#1A1A2E",
        font=dict(color="#B0BEC5", family="Noto Sans TC"),
        xaxis=dict(title="預測時段", gridcolor="#2D2D4E", linecolor="#444", showline=True),
        yaxis=dict(title="降雨機率 (%)", range=[0, 120], gridcolor="#2D2D4E", linecolor="#444", showline=True),
        margin=dict(l=40, r=20, t=60, b=40),
        bargap=0.3,
    )
    return fig


def render_charts_section(df_city: pd.DataFrame, city: str) -> None:
    """
    渲染圖表區塊（儀表板下半部）。
    左欄：氣溫折線圖；右欄：降雨機率長條圖。

    Args:
        df_city : 已篩選為單一縣市的 DataFrame
        city    : 縣市名稱
    """
    st.markdown(f"### 📈 {city}｜氣象預測趨勢")

    col_temp, col_pop = st.columns(2)

    with col_temp:
        fig_temp = build_temperature_chart(df_city, city)
        st.plotly_chart(fig_temp, use_container_width=True)

    with col_pop:
        fig_pop = build_pop_chart(df_city, city)
        st.plotly_chart(fig_pop, use_container_width=True)


# ============================================================
# Section 5：UI 元件層 (UI Components)
# ============================================================

def configure_page() -> None:
    """
    設定 Streamlit 頁面基礎屬性與全域 CSS 樣式。
    必須在所有 st.* 呼叫之前執行。
    """
    st.set_page_config(
        page_title="台灣天氣即時監測儀表板",
        page_icon="🌤️",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # 注入全域 CSS（深色主題 + Google Font）
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;700&display=swap');

    html, body, [data-testid="stAppViewContainer"] {
        background-color: #12121E !important;
        font-family: 'Noto Sans TC', sans-serif;
    }
    [data-testid="stSidebar"] {
        background-color: #1A1A2E !important;
        border-right: 1px solid #2D2D4E;
    }
    h1 { color: #E8EAF6 !important; letter-spacing: 0.5px; }
    h2, h3 { color: #C5CAE9 !important; }

    /* KPI 指標卡片 */
    [data-testid="stMetric"] {
        background: #1E1E2E;
        border: 1px solid #3D3D5C;
        border-radius: 12px;
        padding: 12px 16px;
    }
    [data-testid="stMetricLabel"] { color: #90A4AE !important; font-size: 0.8rem; }
    [data-testid="stMetricValue"] { color: #E8EAF6 !important; font-size: 1.6rem; font-weight: 700; }

    hr { border-color: #2D2D4E !important; }
    footer { visibility: hidden; }
    </style>
    """, unsafe_allow_html=True)


def render_sidebar(df: pd.DataFrame) -> str:
    """
    渲染側邊欄控制面板，回傳使用者選擇的縣市。

    Args:
        df : 完整天氣 DataFrame

    Returns:
        使用者選擇的縣市名稱字串
    """
    with st.sidebar:
        st.markdown("## 🌤️ 台灣天氣監測")
        st.markdown("---")

        # ── 縣市選擇器 ────────────────────────────────────────
        st.markdown("### 🔍 篩選縣市")
        cities = sorted(df["location_name"].unique())
        selected = st.selectbox("選擇縣市", cities, index=0)

        st.markdown("---")

        # ── 資料狀態資訊 ──────────────────────────────────────
        latest_fetch = df["fetched_at"].max() if "fetched_at" in df.columns else "N/A"
        total_records = len(df)

        st.markdown("### 📡 資料狀態")
        st.info(f"**最後更新**\n\n{latest_fetch}")
        st.metric("資料總筆數", f"{total_records} 筆")

        st.markdown("---")

        # ── 圖例說明 ──────────────────────────────────────────
        st.markdown("### 🗺️ 地圖圖例")
        st.markdown(
            "🟢 **低** 降雨機率（< 30%）\n\n"
            "🟠 **中** 降雨機率（30–60%）\n\n"
            "🔴 **高** 降雨機率（> 60%）"
        )

        st.markdown("---")
        st.markdown(
            "<small style='color:#546E7A;'>"
            "資料來源：中央氣象署 CWA<br>"
            "API: F-C0032-001<br>"
            "NCHU AI 課程實作專案</small>",
            unsafe_allow_html=True,
        )

    return selected


def render_header() -> None:
    """渲染頁面主標題與副標題。"""
    st.markdown(
        "<h1 style='text-align:center; padding:0.5rem 0 0.2rem;'>"
        "🌤️ 台灣天氣即時監測儀表板"
        "</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='text-align:center; color:#546E7A; margin-bottom:1rem;'>"
        "資料來源：中央氣象署 Open Data API｜今明 36 小時天氣預報"
        "</p>",
        unsafe_allow_html=True,
    )


def render_kpi_cards(df_city: pd.DataFrame) -> None:
    """
    渲染 KPI 指標卡片列（最近一個時段的摘要資料）。

    Args:
        df_city : 已篩選為單一縣市並依時間排序的 DataFrame
    """
    if df_city.empty:
        return

    first = df_city.iloc[0]
    emoji = get_weather_emoji(first.get("weather_desc"))
    desc  = first.get("weather_desc") or "未知"
    mint  = f"{first['min_temperature']:.0f}" if pd.notna(first.get("min_temperature")) else "--"
    maxt  = f"{first['max_temperature']:.0f}" if pd.notna(first.get("max_temperature")) else "--"
    pop   = f"{first['pop']:.0f}%"            if pd.notna(first.get("pop"))             else "--"

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(f"{emoji} 天氣現象", desc)
    c2.metric("🌡️ 最高溫度",      f"{maxt} °C")
    c3.metric("❄️ 最低溫度",      f"{mint} °C")
    c4.metric("🌧️ 降雨機率",      pop)


def render_footer() -> None:
    """渲染頁尾版權資訊。"""
    st.markdown("---")
    st.markdown(
        "<p style='text-align:center; color:#37474F; font-size:0.8rem;'>"
        "© 2026 台灣天氣監測儀表板｜NCHU AI 課程實作專案｜"
        "資料來源：中央氣象署 CWA Open Data"
        "</p>",
        unsafe_allow_html=True,
    )


# ============================================================
# Section 6：主程式 (Main Orchestrator)
# ============================================================

def main() -> None:
    """
    主程式進入點。

    職責：依序協調所有區塊的渲染，保持邏輯清晰。
    各細節實作已封裝至對應 function，此處僅負責呼叫順序。

    渲染流程：
      configure_page()       → 頁面初始化（必須最先）
      render_header()        → 主標題
      load_data()            → 資料讀取（失敗則 st.stop()）
      render_sidebar()       → 側邊欄控制面板
      render_kpi_cards()     → KPI 摘要卡片
      render_map_section()   → 全台彩色地圖（上半部）
      render_charts_section()→ Plotly 預測圖表（下半部）
      render_footer()        → 頁尾
    """
    # ── 1. 頁面初始化（set_page_config 必須第一行）────────────
    configure_page()

    # ── 2. 主標題 ─────────────────────────────────────────────
    render_header()

    # ── 3. 資料讀取（含防呆 Error Handling）──────────────────
    df = load_data()
    if df is None:
        st.stop()   # 讀取失敗，友善終止，不讓頁面崩潰

    # ── 4. 側邊欄（取得使用者選擇的縣市）────────────────────
    selected_city = render_sidebar(df)

    # 依選擇的縣市篩選並排序（供圖表使用）
    df_city = (
        df[df["location_name"] == selected_city]
        .sort_values("start_time")
        .reset_index(drop=True)
    )

    # ── 5. KPI 指標卡片 ───────────────────────────────────────
    render_kpi_cards(df_city)
    st.markdown("---")

    # ── 6. 上半部：全台彩色地圖 ──────────────────────────────
    render_map_section(df)

    st.markdown("---")

    # ── 7. 下半部：Plotly 統計圖表 ───────────────────────────
    render_charts_section(df_city, selected_city)

    # ── 8. 頁尾 ───────────────────────────────────────────────
    render_footer()


# ── 程式進入點 ───────────────────────────────────────────────
if __name__ == "__main__":
    main()
