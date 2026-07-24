# My Learning Journey

這是一個記錄我技術成長軌跡與專案實踐的個人空間，由 Gemini (Antigravity) 協助規劃與開發。

## 專案架構說明
為了保持專案的可維護性與擴充性，我將專案內容進行了模組化管理：

- `/portfolio/`: 存放各階段的網頁作品集。
- `/assets/`: 存放靜態資源（如個人大頭貼等圖片）。
- `/[YYYYMMDD]/`: 存放每日學習紀錄與筆記。

## 作品集版本 (Portfolio)
目前我的網頁專案包含三個演進版本：

1. **基礎版 (index.html)**: 初始網頁架構與 JavaScript 基礎功能練習。
2. **專業版 (index_pro.html)**: 針對視覺優化與專業 UI/UX 設計。
3. **實驗版 (index_pro_v2.html)**: 採用模組化架構，記錄我進階的技術實踐。

## 快速連結
- [基礎學習頁面](https://hirohirolee.github.io/My-Learning-Journey/portfolio/index.html)
- [專業版 Portfolio](https://hirohirolee.github.io/My-Learning-Journey/portfolio/index_pro.html)
- [實驗版 Portfolio v2](https://hirohirolee.github.io/My-Learning-Journey/portfolio/index_pro_v2.html)

## 開發技術棧 (Tech Stack)
- **前端核心**: HTML5, CSS3, JavaScript (ES6+)
- **版本控制**: Git, GitHub
- **部署環境**: GitHub Pages

2026/05/31 開發日誌：架構優化與功能整合
1. 工作目標
優化目錄結構，將專案檔案分類整理。

實作即時時鐘功能至首頁。

將個人頭像整合至 Hero Section。

解決因路徑變更導致的資源載入錯誤。

2. 開發流程與技術筆記
目錄架構重構：

執行目錄結構調整，將專案檔案歸類至 assets/, portfolio/, daily_lessons/ 資料夾。

使用 Git 進行版本控制：git add . -> git commit -> git push。

解決「資源載入失敗 (404)」問題：

問題描述：檔案移動後，網頁無法正確讀取圖片，顯示破圖。

除錯過程：利用瀏覽器開發者工具 (F12) 的 Console 查看錯誤紀錄，確認是因為相對路徑指向錯誤。

解決方案：將圖片路徑從 assets/avatar.jpg 修改為 ../assets/avatar.jpg，成功跳出當前目錄並正確指向根目錄的資源。

即時時鐘功能：

在 HTML 的 hero-content 中新增 <div id="clock"> 區塊。

透過 JavaScript 定時更新顯示時間。

透過「清空快取並強制重新整理」解決瀏覽器快取導致的更新延遲。

3. 執行指令速查 (Git 實戰)
為了提升效率，已設定 Git 別名：

git config --global alias.pushall '!git add . && git commit -m "update" && git push'

往後只需輸入 git pushall 即可一鍵完成同步。

4. 今日成果截圖紀錄 (建議放置處)
[ ] 截圖 1：調整後的資料夾結構 (展示分類邏輯)。

[ ] 截圖 2：修正圖片路徑前後的 Console 錯誤對比圖。

[ ] 截圖 3：目前已成功顯示頭像與時間的最終網頁畫面。

---
*由 Hiro 開發與維護，持續更新中。*
