# 🍲 文章牛肉湯 - AI 公關與社群分析總管：開發成果總結報告

本專案已成功將原有的命令列腳本，升級重構為一個功能完整、具備多模態視覺與機器學習擴散預估、且基於 **LangGraph 狀態機架構** 運行的「多 Agent 協作網頁平台」，並同步升級了「互動式命令列工具」。

兩者皆支援「離線模擬模式 (Mock Mode)」與「RAG 切片最佳化與磁碟持久化」，完美符合生產與開源發布標準。

---

## 🚀 核心功能亮點

### 1. 🎬 LangGraph 多 Agent 協作工作流 (`web_app.py`)
* 採用 LangGraph `StateGraph` 架構，將整個分析流解耦為多個專業的「Agent 部門（節點）」：
  * **分類部門**：自動判定評論屬性（正面好評 / 負面抱怨）。
  * **情報檢索部門**：依據分類進行 RAG 檢索，並調用機器學習輿情擴散演算法。
  * **公關/行銷部門**：撰寫對應報告草稿（食安危機道歉信 或 熱情社群行銷信）。
  * **品牌監察總監**：嚴格把關公關信質量，若誠意度不足或有法規風險，則自動退回重寫（最多 2 次）。
* **協同對話流視覺化**：在前端利用 Streamlit 聊天室元件渲染部門間的派發、審核、退回等對話紀錄。

### 2. 💬 協同對話微調功能
* 在報告生成後開啟對話聊天框，店家老闆可以直接對 AI 總監發送指令（例如：「*語氣再溫柔一點，並承諾送肉燥飯*」）。
* 系統會以聊天對話形式由 LLM 自動重修報告，並**即時更新**最上方的視覺成果與 Markdown 下載檔案。

### ⚡ 3. 雙通道「離線模擬模式 (Mock Mode)」- 免 API Key 測試
* **網頁版 (`web_app.py`)**：勾選側邊欄開關，無縫啟用模擬流程。
* **指令列版 (`app.py`)**：啟動時如未偵測到金鑰，可按 Enter 直接開啟模擬模式。
* **效果**：兩者皆會繞過 API 呼叫，直接採用本地的高品質模擬資料來運作完整 RAG、Agent 部門協調與報告產出。

### 4. 💾 RAG 向量磁碟持久化與智慧更新
* **持久化儲存 (`chroma_db_laws/`, `chroma_db_menu/`)**：將向量資料庫保存至本地磁碟，再次加載時完全不耗費 API 金鑰，啟動加速至毫秒級。
* **智慧比對更新**：自動偵測原始文字檔的修改時間，只有在 `laws.txt` 或 `menu.txt` 變動時才會在背景自動刪除舊庫並重新編譯更新。

### 5. 🗂️ RAG 資料預處理與 Chunking 切片優化
* **文件清洗 (Document Cleaning)**：自動去除冗餘換行、空白與雜訊字元。
* **重疊切片 (Recursive Character Splitting)**：使用 `RecursiveCharacterTextSplitter` 限制每個切片最大 200 字，並留設 30 字的 `overlap` 重疊區，確保切片邊界處的語意及句子完整度，顯著提升檢索匹配度。

---

## 🔒 GitHub 安全與開源配置

為了保護金鑰隱私並確保專案庫整潔，我們已經配置了：
1. **[.gitignore](file:///c:/Users/admin/Desktop/test/.gitignore)**：
   * 排除 `.env`（保護您的 OpenAI API Key，防止洩漏）。
   * 排除 `chroma_db_laws/` 與 `chroma_db_menu/` 二進位資料庫資料夾。
2. **[.env.example](file:///c:/Users/admin/Desktop/test/.env.example)**：
   * 提供金鑰環境變數模板，讓其他開發者下載您的 GitHub 專案後，複製並命名為 `.env` 填入自己的 API Key 即可。
   * **自動重建機制**：其他開發者在沒有本地 `chroma_db` 資料夾的情況下，首次執行程式時，系統會自動偵測並當場重新讀取文字檔、編譯並建庫，無需任何手動設定。

---

## 📁 檔案變更清單

* **[NEW] [web_app.py](file:///c:/Users/admin/Desktop/test/web_app.py)**：主網頁應用程式（Streamlit + LangGraph）。
* **[NEW] [menu.txt](file:///c:/Users/admin/Desktop/test/menu.txt)**：招牌菜單與菜色特色描述檔。
* **[NEW] [development_summary.md](file:///c:/Users/admin/Desktop/test/development_summary.md)**：本開發成果總結文件。
* **[NEW] [.gitignore](file:///c:/Users/admin/Desktop/test/.gitignore)**：Git 忽略清單。
* **[NEW] [.env.example](file:///c:/Users/admin/Desktop/test/.env.example)**：金鑰配置範本。
* **[MODIFY] [app.py](file:///c:/Users/admin/Desktop/test/app.py)**：重構為**「全功能互動式命令列工具」**（支援離線模擬、磁碟持久化智慧加載、自訂輸入評論、情緒分類與彩色列印）。
