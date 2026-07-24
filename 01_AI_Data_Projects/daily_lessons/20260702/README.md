# 🌤️ 台灣 CWA 天氣資料工程專案

> **NCHU AI 課程實作｜2026-07-02**

本專案示範如何使用 Python 串接台灣中央氣象署 (CWA) Open Data API，抓取天氣預報資料後存入本地 SQLite 資料庫，並透過 Streamlit 建立互動式天氣監測儀表板。

---

## 📁 專案結構

```
20260702/
├── cwa_weather_fetcher.py   # API 串接 + 資料庫寫入主程式
├── app.py                   # Streamlit 天氣儀表板
├── requirements.txt         # 套件需求清單
├── .env.example             # 環境變數範本（安全存放 API Key）
└── .gitignore               # 排除 .env、.db 等敏感/暫存檔
```

---

## 🔑 核心技術重點

| 主題 | 說明 |
|------|------|
| **API 串接** | CWA Open Data RESTful API（F-C0032-001、F-D0047-003） |
| **資安規範** | API Key 透過 `.env` + `python-dotenv` 管理，絕不 hardcode |
| **SSL 處理** | Python 3.12+ 嚴格驗證下的 CWA SSL 憑證相容性解決方案 |
| **資料清理** | `pandas` 數值轉型、時間解析、NaN 防呆 |
| **資料庫** | `sqlite3` 建立本地 DB，`CREATE TABLE IF NOT EXISTS` 冪等設計 |
| **視覺化** | `Plotly` 折線圖 / 長條圖 + `Folium` 互動地圖 |
| **儀表板** | `Streamlit` 深色主題 + 模組化架構 |

---

## 🚀 快速開始

### 1. 安裝套件

```bash
pip install -r requirements.txt
```

### 2. 設定 API 授權碼

```bash
copy .env.example .env
# 開啟 .env，填入您的 CWA API Key
# 申請網址：https://opendata.cwa.gov.tw/user/authkey
```

### 3. 抓取天氣資料

```bash
python cwa_weather_fetcher.py
```

### 4. 啟動儀表板

```bash
streamlit run app.py
```

瀏覽器開啟 **http://localhost:8501**

---

## 📊 儀表板功能

- **側邊欄**：縣市下拉篩選器 + 資料狀態 + 地圖圖例
- **KPI 卡片**：天氣現象、最高/最低溫、降雨機率
- **全台地圖**：OpenStreetMap 彩色底圖，22 縣市圓形標記（綠🟢橘🟠紅🔴三色依降雨機率）
- **氣溫折線圖**：最高/最低溫雙線 + 填色區域
- **降雨機率長條圖**：顏色深淺依機率動態變化

---

## 🗃️ 資料庫結構

### `weather_36h`（今明 36 小時預報）

| 欄位 | 型別 | 說明 |
|------|------|------|
| `location_name` | TEXT | 縣市名稱 |
| `start_time` | TEXT | 預報起始時間 |
| `end_time` | TEXT | 預報結束時間 |
| `weather_desc` | TEXT | 天氣現象 |
| `weather_code` | TEXT | 天氣代碼 |
| `pop` | INTEGER | 降雨機率 (%) |
| `min_temperature` | INTEGER | 最低溫度 (°C) |
| `max_temperature` | INTEGER | 最高溫度 (°C) |
| `fetched_at` | TEXT | 抓取時間戳記 |

---

## ⚠️ 注意事項

- `.env` 檔案已加入 `.gitignore`，**絕對不要 commit 含有真實 API Key 的 .env**
- 資料庫 `weather_data.db` 為本地暫存，也已排除於版控之外
- 每次執行 `cwa_weather_fetcher.py` 都會累積新資料至資料庫（不覆蓋舊資料）
