# Google 地圖自動化爬蟲與資料分析管線 - 後端系統架構說明書 (Backend Technical Architecture)

**文件版本 Document Version**: v1.0  
**目標讀者 Target Audience**: 後端工程師、系統架構師、資料管線開發團隊  
**專案名稱 Project Name**: 自動化地圖與論壇社群評論抓取引擎 (Map & Forum Review Scraper Pipeline)  

---

## 🏗️ 1. 系統整體架構圖 (System Architecture Overview)

本專案採用**高度解耦、模組化與插件驅動 (Plugin-Driven Microkernel Architecture)** 的設計模式。系統將「GUI 互動層」、「非同步爬蟲執行引擎」、「網站解析規則庫」與「資料轉換匯出管線」徹底分離，確保高可擴展性與易維護性。

```
+-----------------------------------------------------------------------------+
|                        UI Presentation Layer (GUI 前端)                      |
|  [ Streamlit App (ui/app.py) ]  <--->  [ Real-time Logs & Queue Monitoring ]|
+-----------------------------------------------------------------------------+
                                       ^  | (Thread-safe Progress & Command Queue)
                                       |  v
+-----------------------------------------------------------------------------+
|                      Controller & Concurrency Layer (控制層)                 |
|  [ ScraperController (core/controller.py) ] --- (Background Threading)      |
|  [ Asyncio Event Loop Management ]          --- (Non-blocking I/O Control)  |
+-----------------------------------------------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------+
|                   Core Automation & Anti-Bot Layer (核心瀏覽器引擎)             |
|  [ Playwright Async API (core/engine.py) ]                                  |
|  [ Stealth & Anti-Bot Mechanics ] --- (--disable-blink-features / UA Mask)  |
+-----------------------------------------------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------+
|                Plugin Registry & Parser Layer (插件化解析層)                  |
|  [ PluginRegistry (core/plugin_registry.py) ] --- (Factory & Registry)      |
|  [ GoogleMapsParser (plugins/google_maps.py) ] --- (BeautifulSoup4 / Regex) |
+-----------------------------------------------------------------------------+
                                          | (Standardized DTO: Post / Comment)
                                          v
+-----------------------------------------------------------------------------+
|                  Data Pipeline & Exporter Layer (資料管線與存檔)               |
|  [ ExporterPipeline (pipeline/exporter.py) ]                                |
|  [ Pandas & OpenPyXL ] ---> [ CSV / Excel (Multi-Sheet) / JSON ]            |
+-----------------------------------------------------------------------------+
```

---

## 🛠️ 2. 核心技術選型與技術棧 (Tech Stack & Libraries)

| 技術模組 | 使用工具與套件 | 後端技術選型理由與優勢說明 |
| :--- | :--- | :--- |
| **自動化瀏覽器引擎** | **Playwright (Python Async API)** | 比傳統 Selenium / Puppeteer 擁有更快的啟動速度與更低的記憶體佔用；支援非同步 (`async/await`) 非阻塞 I/O，能精準等待動態 SPA (單頁應用) 的 AJAX 元件加載。 |
| **DOM 結構解析器** | **BeautifulSoup4 (bs4) + Regex** | 採用高解析效能的 HTML 樹狀語法分析器，搭配正則表達式與 `urllib.parse` 進行網址與標題備援抽取，具備極強的容錯能力。 |
| **資料管線與結構化轉換** | **Pandas + OpenPyXL** | 藉助 Pandas DataFrame 的高效矩陣運算與數據清洗能力，一次性整理主表（景點資料）與關聯明細表（留言明細），並透過 OpenPyXL 輸出多頁籤 Excel。 |
| **即時後台與監控介面** | **Streamlit** | 輕量級 Python 全端框架，無須編寫龐大的前端 JS，即可實現後台監控、批量網址派送與即時終端機日誌流式傳輸 (Real-time Log Streaming)。 |

---

## 🧬 3. 後端主要軟體設計模式與架構特色 (Key Architectural Design Patterns)

### 3.1 插件化與微核心架構 (Plugin Registry & Open-Closed Principle)
* **設計實作**：在 [core/plugin_registry.py](file:///d:/%E8%AB%96%E5%A3%87%E7%88%AC%E8%9F%B2/core/plugin_registry.py) 中利用註冊表模式 (Registry Pattern) 建立統籌中心。
* **對後端協作的意義**：系統完全符合「**開閉原則 (OCP)**」。日後後端團隊若需擴展爬取新目標（例如：PTT、Dcard、Tripadvisor 或 Mobile01），**完全不需要修改任何 core 引擎程式碼**。只需繼承抽象類別 `BaseParser` 寫一個新插件，並以 `@registry.register_parser` 註冊，核心引擎就會自動識別並執行調用！

### 3.2 雙層並發模型與執行緒安全通訊 (Dual-Layer Concurrency & Thread-Safe Queue)
* **設計實作**：前端 Streamlit 屬於同步阻塞式 UI，為了避免爬蟲卡死介面，[core/controller.py](file:///d:/%E8%AB%96%E5%A3%87%E7%88%AC%E8%9F%B2/core/controller.py) 利用 `threading.Thread` 在後台開啟獨立執行緒，並在該執行緒內啟動 `asyncio` 事件迴圈運行的 Playwright 引擎。
* **對後端協作的意義**：採用經典的「**生產者-消費者模型 (Producer-Consumer Model)**」。爬蟲引擎作為生產者，抓取到最新留言或執行日誌時，透過執行緒安全的 `queue.Queue` 推送到緩衝區；前端 GUI 作為消費者安全地取出並渲染。此架構極易移轉為 **Celery + Redis / RabbitMQ** 的非同步任務分散式 worker 模式！

### 3.3 嚴格的資料傳輸物件與型別契約 (DTO & Typed Data Models)
* **設計實作**：在 [models.py](file:///d:/%E8%AB%96%E5%A3%87%E7%88%AC%E8%9F%B2/models.py) 中使用 Python `dataclasses` 定義標準化的資料結構 (`Post`, `Comment`)。
* **對後端協作的意義**：所有不同來源的網站資料，在進入管線後均必須符合此嚴格的 DTO 契約。後端同學可以直接對接此 DTO 進行 資料庫持久化 (ORM Mapping 如 SQLAlchemy / Django ORM)、Elasticsearch 索引匯入或 API JSON Response，無需擔心欄位遺失或型別不一致。

### 3.4 企業級反爬蟲與隱身防護層 (Enterprise Anti-Bot Stealth Layer)
* **設計實作**：[core/engine.py](file:///d:/%E8%AB%96%E5%A3%87%E7%88%AC%E8%9F%B2/core/engine.py) 中配置了多重防禦突破機制：
  1. **Blink 特徵隱蔽**：注入 `--disable-blink-features=AutomationControlled` 關閉自動化偵測標記。
  2. **環境變數覆寫**：在 Page 執行 JavaScript (`add_init_script`) 覆寫 `navigator.webdriver` 屬性。
  3. **自動 UA 清洗**：動態消弭 User-Agent 內的 `Headless` 字樣。
  4. **禮貌性限流 (Politeness Delay)**：[config.py](file:///d:/%E8%AB%96%E5%A3%87%E7%88%AC%E8%9F%B2/config.py) 內建可調控的隨機請求延遲與 `enforce_robots_txt` 規範限制，防範 IP 遭到目標服務器封鎖 (Rate Limiting / IP Ban)。

### 3.5 永久存檔與不覆寫資料管線 (Non-destructive Historical Pipeline)
* **設計實作**：匯出引擎 ([pipeline/exporter.py](file:///d:/%E8%AB%96%E5%A3%87%E7%88%AC%E8%9F%B2/pipeline/exporter.py)) 具備雙重存檔策略。
* **對後端協作的意義**：
  * 每次執行都會自動分析景點標題與當前秒數，產生唯一的 `Run ID`（如 `三媽臭臭鍋_20260725_150709.xlsx`），確保資料具備可追溯性 (Audit Trail) 與歷史快照 (Snapshot)。
  * 支援關聯式資料庫友善的「雙表分離輸出」：主表 (`export.csv`) 儲存景點資訊，明細表 (`export_comments.csv`) 儲存留言與評分明細，方便後端直接透過 Foreign Key (`post_id`) 匯入 SQL 資料庫 (MySQL / PostgreSQL)。

---

## 🔗 4. 後端工程師對接與擴展指南 (How Backend Teams Can Extend This)

1. **如需改為 API Server / 微服務對接 (FastAPI / Django)**：
   * 由於 `ScraperController` 與 `ExporterPipeline` 已經與 GUI 介面完全解耦，後端只需引入 `core/controller.py`，即可直接在 FastAPI Routing 中觸發非同步抓取任務，並透過 REST API 返回 JSON DTO 數據。
2. **如需串接資料庫 (Database Integration)**：
   * 在 [pipeline/exporter.py](file:///d:/%E8%AB%96%E5%A3%87%E7%88%AC%E8%9F%B2/pipeline/exporter.py) 中，繼承 `BaseExporter` 新增一個 `DatabaseExporter` 類別，在 `export(self, posts)` 方法內把 `Post` 與 `Comment` 對象批次 `session.bulk_save_objects()` 寫入資料庫即可。
3. **如需佈署至 Docker / 雲端容器 (Cloud Deployment)**：
   * 本架構的 Playwright 模組已準備妥當，在 Dockerfile 中安裝官方相依套件 (`pip install playwright && playwright install --with-deps chromium`) 即可直接在 Linux Server / AWS ECS 上高效運行無頭抓取。
