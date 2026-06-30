# 🍲 文章牛肉湯 - AI 公關與社群分析總管

本專案是一個基於 **LangGraph 狀態機** 架構運行的「多 Agent 協同公關與行銷分析平台」。
它能自動判定顧客在 Google 地圖上發表的評論（好評/負評），依據評論情緒載入不同 RAG 知識庫，並生成對應的應對報告、寫出道歉信/感謝信。

專案全面支援 **「OpenAI (雲端付費)」** 與 **「Ollama (本地開源免費)」** 雙引擎動態切換，滿足高效能與零預算的不同測試需求。

專案提供以下三種測試與對接通道：
1. 🎨 **Streamlit 網頁測試平台**：模擬公司內部 Agent 對話流，支援一鍵下載報告與**對話式微調修改**。
2. 💻 **互動式命令列工具**：彩色終端預警警報與互動式輸入。
3. 🌐 **REST API 伺服器**：提供 FastAPI 連接埠，供**後端同學（爬蟲）**與**前端同學**對接。

---

## 🚀 核心黑科技

* **雙引擎自由切換 (Hybrid Engine)**：可一鍵切換呼叫 OpenAI 雲端模型（GPT-4o-mini），或完全本地運行、終身免費的開源 LLM（預設為 Ollama 的 `qwen2.5:3b` 與 `nomic-embed-text`）。
* **LangGraph 多部門循環審核**：公關部寫出的信件會被「品牌總監」進行審查。如果誠意度評分低於 88 分或有推諉、法規風險，將自動退回重寫（最多 2 次）。
* **雙庫 RAG 預處理與切片**：
  * **負評** ➔ RAG 匹配《食安法》、《民法》小抄。
  * **好評** ➔ RAG 匹配《文章牛肉湯菜單》推薦合適菜色。
  * **切片策略**：文件經過清洗後，使用 `RecursiveCharacterTextSplitter` 限制每個切片為 200 字，並留設 30 字重疊區（overlap），大幅提升向量檢索精度。
* **向量庫磁碟持久化與隔離**：Chroma 向量庫儲存於本地。本專案為 OpenAI 與 Ollama 隔離了向量目錄（例如：`chroma_db_laws_openai` 與 `chroma_db_laws_ollama`），防止不同引擎的向量維度衝突崩潰。
* **多模態視覺 OCR (Vision)**：支援真實圖片上傳判定（例如湯中有蟲的圖片，在 OpenAI 模式下有效）。
* **輿情擴散風險 ML 演算法**：根據評星、敏感字眼及圖片事證估算網頁發酵的擴散風險（%）。
* **免 Key 雙通道離線模擬模式 (Mock Mode)**：不論網頁或命令列版，未填入 API 金鑰或未啟動 Ollama 時，均可一鍵啟用離線模擬測試。

---

## 📁 專案檔案說明

* `web_app.py`：Streamlit + LangGraph 網頁平台（支援雙引擎與模擬模式切換）。
* `app.py`：互動式命令列（CLI）分析工具（支援雙引擎與模擬模式選取）。
* `api_server.py`：FastAPI REST API 串接伺服器（API 支援指定 engine 參數）。
* `test_api.py`：API 一鍵連線測試腳本。
* `laws.txt`：法規小抄文字檔（負評 RAG 庫）。
* `menu.txt`：招牌菜單描述檔（好評 RAG 庫）。
* `development_summary.md`：開發成果整理報告。
* `.gitignore`：安全防護排除名單（已自動排除 `.env` 金鑰檔與 `chroma_db` 二進位資料庫資料夾，確保 GitHub 上傳安全）。
* `.env.example`：金鑰設定模板。

---

## 🛠️ 安裝與運行指南

### 1. 安裝所有依賴
```bash
pip install -r requirements.txt
```

### 2. 金鑰與本地 Ollama 設定
* **若要使用 OpenAI 模式**：
  複製 `.env.example` 並重新命名為 `.env`，接著填入您的金鑰：
  ```env
  OPENAI_API_KEY=您的_sk-proj-真實OpenAI_Key
  ```
* **若要使用 Ollama 本地模式**：
  請下載安裝 [Ollama](https://ollama.com/)。安裝後，開啟終端機拉取專案所使用的免費開源大腦與翻譯官模型：
  ```bash
  # 拉取語言模型大腦 (建議使用更輕快適合一般電腦的 qwen2.5:3b)
  ollama pull qwen2.5:3b
  
  # 拉取翻譯官向量模型 (預設使用 nomic-embed-text)
  ollama pull nomic-embed-text
  ```
  *(確保 Ollama 在背景運行中，預設埠為 11434)*

### 3. 執行網頁版測試
```bash
streamlit run web_app.py
```
預設網址：`http://localhost:8501`（可於側邊欄選擇 OpenAI、Ollama 或 模擬模式）。

### 4. 執行命令列版測試
```bash
python app.py
```
根據控制台選單提示進行引擎選擇。

### 5. 啟動 REST API 伺服器 (供前後端對接)
```bash
python api_server.py
```
伺服器將啟動在：`http://127.0.0.1:8000`

### 6. 一鍵測試 API 連線
確保 API 伺服器已啟動，另開終端機執行：
```bash
python test_api.py
```
本腳本會發送模擬請求，驗證 API 伺服器是否連線正常。

### 7. 線上互動式 Swagger UI 測試文件
伺服器啟動後，在瀏覽器輸入以下網址即可在線上直接測試與發送 API 請求：
```text
http://127.0.0.1:8000/docs
```

---

## 🌐 API 串接規格說明 (供前後端對接)

### 【POST】分析 Google 評論與生成應對策略
* **網址**：`http://127.0.0.1:8000/api/analyze`
* **Content-Type**：`application/json`
* **請求範本 (JSON Body)**：
  ```json
  {
    "review": "慕名去吃台南文章牛肉湯，喝到一半發現湯裡竟然有一隻蒼蠅！店員態度還差到爆！",
    "rating": 1,
    "image_base64": null,
    "tone": "標準",
    "engine": "openai",
    "mock_mode": false
  }
  ```
  * **參數細節**：
    * `engine`: 可填入 `"openai"` 或 `"ollama"`。
    * `mock_mode`: 設為 `true` 將直接回傳模擬數據，不消耗 OpenAI API 或本機算力。

* **回傳範本 (JSON Response)**：
  ```json
  {
    "sentiment": "負面",
    "risk_percent": 84.0,
    "scores": {
      "SINCERITY": 95,
      "LEGAL_DEFENSE": 90,
      "REPUTATION_RECOVERY": 92
    },
    "report_content": "### 📊 1. 危機評估\\n* **危機等級**：🔴 高...（完整的 Markdown 公關應對報告）",
    "is_mock_run": false,
    "engine_used": "openai",
    "review_history": [
      "✅ 第 1 次審查通過。"
    ]
  }
  ```
