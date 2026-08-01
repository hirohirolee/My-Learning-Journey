# 🚀 Streamlit Cloud 雲端部署與本地運行指南

本文件說明如何將本專案部署至 **Streamlit Community Cloud**，或在您的本地電腦進行設定與運行。

---

## 💻 1. 本地運行指南 (Local Run Guide)

若要在您的電腦上啟動此互動平台，請遵循以下步驟：

### 步驟一：確保安裝 Python 環境
本專案支援 Python 3.9+ 以上版本。請在終端機中確認 Python 安裝狀態：
```bash
python --version
```

### 步驟二：安裝相依套件
在工作目錄 `daily_lessons/20260609/huanclass/` 下，執行以下指令以安裝所有必要的機器學習與視覺化套件：
```bash
pip install -r requirements.txt
```

### 步驟三：啟動 Streamlit 應用程式
執行以下指令來開啟網頁應用程式：
```bash
streamlit run app.py
```
啟動後，瀏覽器會自動開啟網址 `http://localhost:8501`。如果沒有自動開啟，請手動複製該網址至瀏覽器。

---

## ☁️ 2. Streamlit Community Cloud 部署指南 (Cloud Deployment Guide)

Streamlit Community Cloud 提供一鍵部署服務，與您的 GitHub 儲存庫無縫對接。

### 部署步驟：

1. **推送代碼至 GitHub**：
   確認本目錄下的所有檔案（特別是 `app.py`、`requirements.txt`、`50_Startups.csv` 以及各個 `.pkl` 模型檔案）都已推送至您的 GitHub 儲存庫 `My-Learning-Journey` 的主分支上。

2. **登入 Streamlit Cloud**：
   使用您的 GitHub 帳號登入 [Streamlit Share](https://share.streamlit.io/)。

3. **點擊 New App（建立新應用）**：
   * **Repository**：選擇您的 `hirohirolee/My-Learning-Journey` 儲存庫。
   * **Branch**：選擇 `master` (或 `main`)。
   * **Main file path**：輸入 `daily_lessons/20260609/huanclass/app.py`（這點非常重要，因為 `app.py` 位於嵌套的子資料夾中）。

4. **點擊 Deploy！**：
   * Streamlit Cloud 將在背景啟動容器。
   * 系統會自動讀取同目錄下的 `requirements.txt`，並自動安裝包含 `plotly`、`scikit-learn` 與 `seaborn` 等套件。
   * 靜候 1-2 分鐘後，即可在專屬的網址上即時體驗您的 AI 平台！

---

## 🔒 3. 注意事項與故障排除 (Troubleshooting)

* **數據加載錯誤 (FileNotFoundError)**：
  專案預設載入 `50_Startups.csv` 與訓練好的模型（如 `rf_model.pkl` 等）。請確保這些檔案與 `app.py` 放在相同的子目錄下，否則部署時會發生路徑尋找錯誤。
* **自訂數據結構**：
  在雲端上使用「資料庫設定」上傳自訂 CSV 數據時，上傳的 CSV 檔案欄位名稱必須完全包含：`R&D Spend`、`Administration`、`Marketing Spend`、`State`、`Profit`，否則重訓管線會報錯。
