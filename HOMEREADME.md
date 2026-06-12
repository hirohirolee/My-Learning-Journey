# 🚀 My Learning Journey

歡迎來到我的學習歷程庫！這是我參加 **2026 NCHU AI 創產培訓班** 期間，所有開發專案與課程練習的歸檔。本專案由 Gemini (Antigravity) 協助規劃與開發，紀錄了我從網頁開發新手到建立專業技術形象的成長歷程與專案實踐。

---

## 📂 專案架構與目錄說明
為了保持專案的可維護性與擴充性，專案內容進行了模組化管理：

| 資料夾/檔案名稱 | 內容說明 |
| :--- | :--- |
| **`/portfolio/`** | 存放各階段的網頁作品集與個人展示區。 |
| **`/assets/`** | 存放所有網站使用的素材（如大頭貼、課程圖示、背景圖片等）。 |
| **`/daily/`** 或 **`/[YYYYMMDD]/`** | 每日課程練習代碼與學習紀錄，依日期分層管理（YYYY-MM-DD）。 |

---

## 🌐 網站連結與作品預覽 (Portfolio)
1. 目前我的網頁專案包含多個演進版本與練習作品：

     * **[基礎學習頁面 / Hello Web Page](https://hirohirolee.github.io/My-Learning-Journey/portfolio/index.html)**
         * 初始網頁架構與 JavaScript 基礎功能練習（用於完成 HW1 作業）。
     * **[個人介紹網頁 (Personal Web)](https://hirohirolee.github.io/My-Learning-Journey/portfolio/person-web/)**
         * 運用 HTML/CSS 打造的專業 Fusion 風格作品集。
 
2. 動態 AI 應用 (Streamlit Cloud)
     這些應用展示了您運用 API 串接與 AI 邊緣運算技術的實作成果，點擊即可即時體驗：

     AI Image App (v20260604)  整合 Puter.js 技術的穩定版生圖工作室。
         https://my-learning-journey-a9egpqgpvwec9kup8grj6x.streamlit.app/

# 🚀 My Learning Journey

歡迎來到我的學習歷程庫！這是我參加 **2026 NCHU AI 創產培訓班** 期間，所有開發專案與課程練習的歸檔。本專案由 Gemini (Antigravity) 協助規劃與開發，紀錄了我從網頁開發新手到建立專業技術形象的成長歷程與專案實踐。

---

## 📂 專案架構與目錄說明
為了保持專案的可維護性與擴充性，專案內容進行了模組化管理：

| 資料夾/檔案名稱 | 內容說明 |
| :--- | :--- |
| **`/portfolio/`** | 存放各階段的網頁作品集與個人展示區。 |
| **`/assets/`** | 存放所有網站使用的素材（如大頭貼、課程圖示、背景圖片等）。 |
| **`/daily/`** 或 **`/[YYYYMMDD]/`** | 每日課程練習代碼與學習紀錄，依日期分層管理（YYYY-MM-DD）。 |

---

## 🌐 網站連結與作品預覽 (Portfolio)
1. 目前我的網頁專案包含多個演進版本與練習作品：

     * **[基礎學習頁面 / Hello Web Page](https://hirohirolee.github.io/My-Learning-Journey/portfolio/index.html)**
         * 初始網頁架構與 JavaScript 基礎功能練習（用於完成 HW1 作業）。
     * **[個人介紹網頁 (Personal Web)](https://hirohirolee.github.io/My-Learning-Journey/portfolio/person-web/)**
         * 運用 HTML/CSS 打造的專業 Fusion 風格作品集。
 
2. 動態 AI 應用 (Streamlit Cloud)
     這些應用展示了您運用 API 串接與 AI 邊緣運算技術的實作成果，點擊即可即時體驗：

     AI Image App (v20260604)  整合 Puter.js 技術的穩定版生圖工作室。
         https://my-learning-journey-a9egpqgpvwec9kup8grj6x.streamlit.app/

     Linear AI App (v20260605)  課程練習與 AI 技術整合展示。
         https://hiro-linear-regression.streamlit.app/

     ML Algorithms & Emotion AI App (v20260608)  結合臉部表情偵測與互動式數學沙盒，動態偵測專注與困惑度，由 AI 導師進行演算法解說。
         https://my-learning-journey-fa32pwgnj5bn8ccq2gabte.streamlit.app/

     50 Startups Profit Regression App (v20260609)  基於 CRISP-DM 的新創公司利潤預測與多模型效能分析，已優化為投影級大圖表、對數尺度與多選演算法過濾（可於本地以 `streamlit run app.py` 運行，已完成 Cloud 部署路徑相容性設定）。
         https://my-learning-journey-x3iuqegsphhxdmrvrzvfry.streamlit.app/

4. 多媒體與音訊轉換應用 (Multimedia)
     * **PDF to Voice Video (v20260612)**：使用 Python 結合 gTTS 語音生成與 pdf2image 投影片擷取，運用 moviepy 自動合成動態簡報播放 `.mp4` 影片。

### 🔗 專案原始碼
* **GitHub Repo**: [https://github.com/hirohirolee/My-Learning-Journey](https://github.com/hirohirolee/My-Learning-Journey)

---

## 🛠 開發技術棧 (Tech Stack)
* **前端核心 (Frontend)**: HTML5, CSS3, JavaScript (ES6+)
* **版本控制與工具**: Git, GitHub, VS Code, Antigravity
* **部署環境 (Deployment)**: GitHub Pages

---

## 📝 核心開發重點與除錯紀錄

### 基礎開發階段
1. **環境建立**: 安裝與設定 Antigravity。
2. **AI 協作**: 使用 AI 產生 `index.html`、`style.css` 及 `script.js`。
3. **時序管理**: 透過 `DOMContentLoaded` 確保 DOM 與 JS 邏輯正確連結。
4. **排版設計**: 使用 Flexbox 進行響應式排版與現代化配色方案。
5. **部署優化**: 解決 GitHub Pages 快取同步問題，建立開發部署工作流（將檔案遷移至 `portfolio/` 資料夾並部署）。

### 2026/05/31：架構優化與功能整合
* **工作目標**：優化目錄結構與路徑，實作即時時鐘與頭像整合。
* **資源載入除錯**：修復檔案移動後的相對路徑，將 `assets/avatar.jpg` 改為 `../assets/avatar.jpg` 解決 404 破圖。
* **Git 實戰別名**：設定 `git config --global alias.pushall '!git add . && commit -m "update" && git push'` 簡化同步。

### 2026/06/04：AI 影像生成與相依套件部署
* **實作技術**：Streamlit + Hugging Face Inference API (`nvidia/Cosmos3-Super-Text2Image`)。
* **安全機制**：實作雙重 API Key 驗證機制（優先讀取系統 Secret `st.secrets.get`，若無則降級為網頁 Password Input），並設定 `.gitignore` 防止敏感金鑰外洩。

### 2026/06/05：線性迴歸分析與異常值偵測
* **實作技術**：`numpy`, `pandas`, `scikit-learn`, `matplotlib`。
* **核心挑戰**：對隨機生成的線性資料進行建模，並利用殘差 (Residuals) 分析自動過濾出偏離最大的前 20 個極端值，在圖表上用紅點標記排名，以可視化評估模型。

### 2026/06/08：十大機器學習演算法與表情感知 AI
* **實作技術**：`face-api.js` + `Gemini API` + `Streamlit`。
* **亮點功能**：
  * 在前端利用 Canvas 動態繪製與互動演算法邊界（如 SVM、KNN、K-Means 等）。
  * 引入 `face-api.js` 追蹤表情以分析專注度與困惑度，動態觸發 AI 助教的語意引導。
  * 利用 `MutationObserver` 解決 Streamlit 跨域 `iframe` 的相機與麥克風授權阻擋政策，完美實現全版流暢體驗。

### 2026/06/09：CRISP-DM 50 Startups 利潤預測與重構
* **實作技術**：`plotly` + 多迴歸模型（Linear, Ridge, SVR, Random Forest, Gradient Boosting）。
* **極端值處理**：利用四分位距 (IQR) 分析剔除 Index 49 利潤極端值（\$14,681.40），並對地區進行 One-Hot 編碼（`drop_first=True`）以防止虛擬變數陷阱。
* **效能重構**：將原本耗時 2 秒的單筆迴圈搜尋演算法改寫為**向量化批量運算 (Vectorized Batch Processing)**，將響應時間降低至 **5 毫秒以內**，徹底消除 UI 卡頓。
* **自訂上傳與重訓**：整合側邊欄上傳功能，支援動態重訓 5 種模型並實時更新 Plotly 互動圖表。

### 2026/06/10：Python 邏輯控制與演算法練習
* **實作內容**：
  * **凱薩密碼加密**：以 `random.seed(10)` 對大小寫英文字母表進行洗牌，實作位移加密與循環回繞邏輯。
  * **座位座位編排**：支援每排 2~7 人的自訂座位編排，並以格式化對齊字串輸出座位表。
  * **質數判斷與迴圈**：實作質數檢驗演算法，並使用平方根 `val ** 0.5` 進行因數尋找範圍優化。
  * **二分搜尋猜數字**：開發 1~100 猜數字遊戲，具備輸入錯誤防護機制，並動態縮小上下限區間。

### 2026/06/12：投影級大圖表重構、互動優化與多媒體音訊影片轉換
* **Streamlit AI 平台優化**：
  * **投影大圖表重構**：重構頂部為單一佔寬 80% 的 **"Top 10 ML Algorithms: MSE vs. Feature Count"** 主圖表，配置投影幕特大字級與右上圖例。
  * **線條擠壓與互動防護**：加入 **Log Scale 對數尺度** 切換（預設開啟）與 **演算法多選篩選器**，完美分離 SVR 高 MSE 所擠壓的其餘 9 種算法線段；加粗折線至 `3.5`，配置 `x unified` 提示對照。
  * **路徑相容性修復**：改採與腳本檔案同目錄的絕對路徑讀取 `50_Startups.csv`，防止 Streamlit Cloud 部署發生 FileNotFoundError。
* **PDF 語音視訊動畫化**（多媒體轉換）：
  * **音視訊合成**：整合 `gTTS`（文字轉語音）與 `pdf2image`（投影片擷取），使用 `moviepy` 自動合成配有語音導讀與切換動畫的 `.mp4` 簡報影片。
