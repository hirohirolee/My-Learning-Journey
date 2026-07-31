# Google 地圖與論壇評論自動化抓取系統 - 支援平台與擴展指南 (Supported Platforms & Extension Guide)

**文件版本 Document Version**: v1.0  
**目標讀者 Target Audience**: 專案經理、資料分析師、後端與爬蟲開發工程師  
**專案位置 Project Root**: `d:\論壇爬蟲`  

---

## 🟢 一、 系統「目前已內建支援」的 3 大平台 (Currently Supported Platforms)

本系統核心內建了微核心插件路由機制 (`PluginRegistry`)，在 `plugins/` 目錄中已預先寫好並註冊了台灣最主流的三大評論與社群網站解析器。使用者只需在 Streamlit GUI 介面或命令行中貼入目標網址，系統即可自動路由至對應的解析器進行抓取與結構化匯出。

| 平台名稱 | 網址路由網域 | 負責插件檔案 | 支援抓取欄位與特殊處理機制 |
| :--- | :--- | :--- | :--- |
| 📍 **Google 地圖 (Google Maps)** | `google.com` | `plugins/google_maps.py` | <ul><li>**抓取重點**：景點/商家名稱、星等評分、評論者姓名、留言文字內容、發布時間（相對時間解碼）。</li><li>**防禦突破**：內建 Playwright `--disable-blink-features` 隱身參數、自動清除 UA 機器人標記與 `navigator.webdriver` 覆寫，完整繞過 Lite Mode (精簡版面) 攔截。</li><li>**標題容錯**：當 DOM 標題為通用字樣或空白時，自動執行中文 URL 解碼分析 (`/place/<Place_Name>/`)。</li></ul> |
| 💬 **PTT 批踢踢實業坊** | `ptt.cc` | `plugins/ptt.py` | <ul><li>**抓取重點**：文章標題、發文者 ID、發文時間、正文內容，以及**下方所有推文、噓文與箭頭留言 (Push Comments)** 列表。</li><li>**年齡檢核突破**：內建自動偵測並繞過「滿 18 歲年齡驗證 (`over18`)」提示畫面，無須手動設定 Cookie 即可直接存取八卦板 (`Gossiping`) 等限制看板。</li></ul> |
| 🎓 **Dcard 狄卡** | `dcard.tw` | `plugins/dcard.tw` | <ul><li>**抓取重點**：文章標題、發文者暱稱 / 學校卡稱 ID、發文時間 (ISO 格式自動轉化)、正文內容與回覆討論串。</li><li>**結構化解析**：支援 Dcard API JSON 結構化回應或標準網頁 DOM 樹狀解析。</li></ul> |

---

## 🌟 二、 後續推薦擴展的目標評論網站 (Recommended Platforms for Extension)

得益於專案嚴謹的「**插件化架構 (Plugin-Driven Architecture)**」與 `BaseParser` 抽象契約，團隊（或後端工程師）將來若要新增支援任何新的網站，**完全不用修改底層核心引擎 (`core/`) 或匯出管線 (`pipeline/`)**。只要花 15~30 分鐘撰寫一個獨立的新模組即可順利掛載。

以下為針對不同商業輿情分析與市場調查需求，最推薦擴展抓取的網站矩陣：

### 1. 🍽️ 美食、食記與餐廳指南網
* **愛食記 (ifoodie.tw)**：台灣市佔率最高的在地美食探店與評分平台，具備高度精準的商圈與餐廳評分數據。
* **窩客島 (WalkerLand.com.tw)**：以深度開箱文、圖文食記與食家評分為主的評論網路。
* **OpenRice 開飯喇 (openrice.com)**：港台知名老牌餐廳搜尋與真實食客評論網。

### 2. 🏨 旅遊訂房與觀光景點評價 (OTA Platforms)
* **Tripadvisor 貓途鷹 (tripadvisor.com.tw)**：全球最具權威的多國語言觀光景點、餐廳與飯店用戶真實評論網，為觀光輿情與旅客體驗分析的黃金資料庫。
* **Agoda / Booking.com**：真實入住房客的星等評分與「優點 / 缺點」分段式文字評論。

### 3. 🛍️ 電商商品與買家滿意度評價
* **蝦皮購物 (Shopee.tw)**：賣場商品頁面下的買家 1~5 星評分、附圖評價與詳細文字使用回饋。
* **momo 購物網 / PChome 24h 購物**：3C 家電、生活百貨消費者的真實開箱與使用後評價。

### 4. 🚗 綜合產業與專業開箱論壇
* **Mobile01 (mobile01.com)**：台灣最具影響力的 3C 商品、汽機車試駕、房地產與家電開箱論壇，文章下方的樓層回覆常包含深度除錯與真實用戶長期使用心得。
* **巴哈姆特 (gamer.com.tw)**：電玩遊戲、動漫娛樂相關的哈啦區心得與玩家評價。

---

## 👨‍💻 三、 後端同學快速開發新插件教學 (Quick-Start Guide to Add a New Plugin)

如需為新網站（例如：**愛食記 iPeen / ifoodie.tw**）開發專屬爬蟲，只需依循以下 4 個簡單步驟：

### Step 1：在 `plugins/` 目錄下建立新檔案
例如建立 `plugins/ifoodie.py`。

### Step 2：繼承 `BaseParser` 並實作 `parse()` 方法
引入 `BeautifulSoup` 或 `json` 解析器，將網頁內容提取為系統標準的 `Post` 與 `Comment` 資料傳輸物件 (DTO)：

```python
import logging
from datetime import datetime
from bs4 import BeautifulSoup
from core.plugin_registry import BaseParser, registry
from models import Post, Comment

logger = logging.getLogger(__name__)

class IFoodieParser(BaseParser):
    def parse(self, html: str, url: str) -> Post:
        soup = BeautifulSoup(html, "html.parser")
        
        # 1. 抽取景點/餐廳標題
        title_tag = soup.find("h1", class_="restaurant-title")
        title = title_tag.text.strip() if title_tag else "IFoodie Restaurant"
        
        # 2. 抽取餐廳整體星等
        rating = 4.5  # 可自 DOM 抽取數字
        
        # 3. 抽取下方食記或留言列表
        comments: list[Comment] = []
        review_elements = soup.find_all("div", class_="review-item")
        for idx, rev in enumerate(review_elements):
            author = rev.find("span", class_="author-name").text.strip()
            content = rev.find("div", class_="review-content").text.strip()
            comments.append(Comment(
                id=f"{url}_rev_{idx}",
                post_id=url,
                author=author,
                content=content,
                rating=5.0,
                created_at=datetime.utcnow()
            ))
            
        # 4. 回傳標準 Post 結構
        return Post(
            id=url,
            forum_name="ifoodie",
            url=url,
            title=title,
            author="System",
            content=f"愛食記餐廳評分摘要：{title}",
            created_at=datetime.utcnow(),
            rating=rating,
            comments=comments
        )

# Step 3：在檔案底部自動註冊網域路由
registry.register_parser("ifoodie.tw", IFoodieParser)
```

### Step 4：在 `plugins/__init__.py` 中引入模組
在 `plugins/__init__.py` (或系統載入入口) 加入一行 `import plugins.ifoodie`，即可大功告成！

**完成！** 
從此刻起，只要在 GUI 介面上貼上任何 `https://ifoodie.tw/...` 的網址，系統就會自動調用新寫好的 `IFoodieParser` 執行隱身抓取，並自動產出不被覆蓋的歷史 Excel 表格與 CSV 明細檔案！
