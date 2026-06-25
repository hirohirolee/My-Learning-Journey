# 🐳 企業數位韌性 AI 導航系統 - Docker 一鍵部署指南

本文件引導您如何在本地電腦或地端伺服器上使用 Docker 與 Docker Compose 一鍵啟動並部署本系統。

---

## 📌 前置準備

1. **安裝 Docker Desktop**：
   - 請前往 [Docker 官網](https://www.docker.com/products/docker-desktop/) 下載並安裝適用於您作業系統的版本。
2. **啟動 Ollama (地端 LLM，選用)**：
   - 若要使用地端私有化 AI 推理，請確保宿主機已啟動 Ollama 且模型已加載成功（預設模型為 `qwen2.5:14b`）：
     ```bash
     ollama run qwen2.5:14b
     ```

---

## 🚀 部署步驟

### 步驟 1：開啟終端機並切換至專案根目錄
請開啟 PowerShell 或 CMD，執行以下命令：
```bash
cd /d d:\My-Learning-Journey\resilience_ai
```

### 步驟 2：設定環境變數
請在專案根目錄下確認 `.env` 檔案存在。若有需要使用雲端備援 API，請填入您的 Gemini API 金鑰：
```env
GEMINI_API_KEY=your_gemini_api_key_here
```
*(提示：`OLLAMA_URL` 預設已在 `docker-compose.yml` 中配置指向宿主機的 `http://host.docker.internal:11434`。)*

### 步驟 3：一鍵構建與啟動容器
在終端機中執行以下指令，在背景編譯並啟動前後端容器：
```bash
docker-compose up --build -d
```
- `-d` 參數表示在背景（Detached mode）運行。
- `--build` 確保當代碼有更新時重新構建鏡像。

---

## 🎯 驗證與存取

啟動完成後，您可以使用瀏覽器存取以下服務：

*   **Streamlit 前端網頁儀表板**：
    👉 **[http://localhost:8501](http://localhost:8501)**
*   **FastAPI 後端 API 自動化文件**：
    👉 **[http://localhost:8000/docs](http://localhost:8000/docs)** (亦可訪問 `/redoc`)

---

## 💾 資料持久化 (Data Persistence)

本地的 ChromaDB 向量庫與審計簽核紀錄目錄已被掛載至宿主機中：
- `./audit_db` ──> `/app/audit_db`
- `./vector_db` ──> `/app/vector_db`

這代表**即使您重構或刪除 Docker 容器，您所有的歷史審計紀錄與知識庫內容都絕對不會遺失**。

---

## 🛑 停止服務

若要暫停系統運行並移除容器，請在專案根目錄下執行：
```bash
docker-compose down
```
