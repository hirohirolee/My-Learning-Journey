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

     AI Image Generation Web App (v20260604)  整合 Puter.js 技術的穩定版生圖工作室。
         https://my-learning-journey-a9egpqgpvwec9kup8grj6x.streamlit.app/

     Linear AI App (v20260605)  課程練習與 AI 技術整合展示。
         https://hiro-linear-regression.streamlit.app/

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

### 2026/05/31 開發日誌：架構優化與功能整合

#### 1. 工作目標
* 優化目錄結構，將專案檔案分類整理。
* 實作即時時鐘功能至首頁。
* 將個人頭像整合至 Hero Section。
* 解決因路徑變更導致的資源載入錯誤。

#### 2. 開發流程與技術筆記
* **目錄架構重構**：執行目錄結構調整，將專案檔案歸類至 `assets/`, `portfolio/`, `daily_lessons/` 資料夾。使用 Git 進行版本控制：`git add .` -> `git commit` -> `git push`。
* **解決「資源載入失敗 (404)」問題**：
    * *問題描述*：檔案移動後，網頁無法正確讀取圖片，顯示破圖。
    * *除錯過程*：利用瀏覽器開發者工具 (F12) 的 Console 查看錯誤紀錄，確認是因為相對路徑指向錯誤。
    * *解決方案*：將圖片路徑從 `assets/avatar.jpg` 修改為 `../assets/avatar.jpg`，成功跳出當前目錄並正確指向根目錄的資源。
* **即時時鐘功能**：
    * 在 HTML 的 `hero-content` 中新增 `<div id="clock">` 區塊。
    * 透過 JavaScript 定時更新顯示時間。
    * 透過「清空快取並強制重新整理」解決瀏覽器快取導致的更新延遲。

#### 3. 執行指令速查 (Git 實戰)
為了提升效率，已設定 Git 別名：
```bash
git config --global alias.pushall '!git add . && git commit -m "update" && git push'
