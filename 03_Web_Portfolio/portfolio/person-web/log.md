# Vercel 與 Streamlit 部署實務教學紀錄

本文件記錄了如何將個人靜態作品集網站與 Python (Streamlit) 練習專案，透過 GitHub 進行分流管理的自動化部署（CI/CD）完整架構與操作流程。

## 🎯 核心部署策略

為了達到最高的運行效率與最簡化維護成本，採用「**前後端分流管理**」策略：

| 專案類型 | 推薦平台 | 架構特點 | 適用場景 |
| :--- | :--- | :--- | :--- |
| **前端作品集 / 個人官網** | **Vercel** | 靜態網頁託管、全球 CDN 加速、免費 SSL | `portfolio/person-web` (HTML/CSS/JS) |
| **Python 練習 / AI 應用** | **Streamlit Cloud** | 常駐型 Python 伺服器、數據視覺化整合 | `daily_lessons/` (如 NCHU AI 課程練習) |

---

## 📂 GitHub 單一事實來源 (Single Source of Truth) 目錄規劃

建議將所有學習資產整合在同一個 GitHub 儲存庫中，並透過子目錄進行分流：

```text
/My-Learning-Journey
├── README.md              # 整個專案的總介紹（可放上 Vercel 與 Streamlit 的成果連結）
├── .gitignore             # 關鍵設定！排除無用或敏感檔案（如 __pycache__, .env, .DS_Store）
├── /portfolio
│   └── /person-web        # 個人靜態網站原始碼 (Vercel 部署目標路徑)
│       ├── index.html     # 首頁（確保副檔名為 .html，Vercel 才能正確抓取）
│       └── ai-studio.html # AI 專案導覽頁面
└── /daily_lessons         # 依照上課日期 (YYYY-MM-DD) 排列的 Python/Streamlit 練習
    ├── /2026-05-15_intro
    │   ├── app.py
    │   └── requirements.txt
    └── /2026-06-08_ai-project
        ├── app.py         # Streamlit 主程式
        └── requirements.txt # Streamlit Cloud 安裝套件的依據
🚀 Vercel 部署個人網站步驟說明
【第一階段：帳號註冊與連動】
前往 Vercel 官網，點選 Continue with GitHub 進行單一登入（SSO）。

跳轉至 GitHub 授權頁面，點擊 Install 安裝 Vercel GitHub App，並選擇開放的儲存庫權限（建議選 All repositories 或單獨勾選 My-Learning-Journey）。

【第二階段：專案匯入與子目錄設定】
成功進入 Vercel 後台後，在專案清單中找到 My-Learning-Journey，點擊 Import。

關鍵步驟（Root Directory）：在部署組態設定頁面中，點擊 Root Directory 旁邊的 Edit，將路徑指定為：
portfolio/person-web
(註：這樣 Vercel 就只會打包該網頁資料夾，不會受其他 Python 檔案干擾)

點擊 Continue 回到主頁面，確認無誤後直接點擊 Deploy。

【第三階段：成功上線與維護】
部署完成後，Vercel 會產出專屬的公開永久網址（例如：https://my-learning-journey-liart.vercel.app）。

右下角工具列 (Vercel Toolbar)：僅有網頁擁有者在登入狀態下看得到，提供線上評論、手機版模擬等測試功能，一般外部訪客看不見。如不需要可點擊 Dismiss 隱藏。

🔄 現代化開發工作流：CI/CD 自動化
當此架構建立完成後，未來的網頁更新流程將完全自動化：

本地端修改：在本機電腦的 portfolio/person-web 資料夾中修改 HTML/CSS 檔案。

推送到 GitHub：執行 Git 指令：

Bash
git add .
git commit -m "優化個人網站介面"
git push origin main
雲端自動部署：Vercel 會在偵測到 GitHub 更新時立即接手，自動重新編譯並更新上線。若新版程式有誤，亦可在 Vercel 後台一鍵執行 Rollback (復原) 回到上一個穩定版本。

本教學文件產生於 2026 年 6 月，記錄 Hiro Lee (李昶漢) 之雲端架構打通過程。
