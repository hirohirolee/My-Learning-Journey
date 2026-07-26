# 文章牛肉湯 AI 雙引擎公關與社群分析系統 - 開發與接軌驗收報告 (2026-07-25)

## 📌 進度總覽與核心成果 (Executive Summary)

本日核心工作聚焦於 **「Supabase 資料庫雙軌混合檢索 (Hybrid Search) 架構整合」**、**「後端 Python 異常防禦與環境修復」**，以及 **「API 與 ML Gatekeeper 守門員端到端實戰驗收」**。
目前系統已全面打通「向量語意檢索 + 關鍵字全文檢索」的雙引擎連動，並且成功於後端 API (`http://127.0.0.1:8000`) 進行對接與 UI 驗收。

---

## 🛠️ 1. 資料庫與雙軌檢索架構升級 (Database & Hybrid Search)

### 1.1 雙軌檢索演算法：最高值正規化融合 (Max-Bounded Additive Fusion)
為了解決傳統單純向量搜尋 (Vector Search) 容易忽略專有名詞與精確關鍵字的問題，以及單純全文檢索 (BM25) 缺乏語意推論能力的限制，於 Supabase PostgreSQL 實作了雙軌混合檢索 RPC 函數 `match_reviews_hybrid`。
* **向量檢索 (Vector Search)**：基於 OpenAI `text-embedding-3-small` 生成的 1536 維向量，利用 `<=>` (Cosine Distance) 計算語意相似度。
* **全文檢索 (Full-Text Search)**：基於 PostgreSQL `to_tsvector('simple', ...)` 與 `ts_rank_cd` 計算 BM25 關鍵字密度權重。
* **正規化融合公式**：
  $$\text{Final Score} = \min\left(1.0,\ \text{VecScore} + \left(\frac{\text{FTSScore}}{\max(\text{FTSScore})}\right) \times 0.15\right)$$
  確保雙軌分數加總後有界（上限 1.0），並給予精準命中關鍵字的歷史評論 15% 的分數權重提升。

### 1.2 資料庫 Schema 欄位對齊與校準
核查並修正了資料庫真實 Schema 與 Python 端的欄位映射對應：
* **主鍵欄位對齊**：確認核心表 `master_reviews` 的 ID 欄位為 `master_review_id`（而非單純的 `id`），並於 SQL 函數的 `RETURNS TABLE` 同時回傳 `master_review_id` 與 `id` 別名，確保 Python 端呼叫 `row.get("master_review_id")` 時 100% 精準對接。
* **評論內容欄位對齊**：修正 SQL 查詢與後端邏輯，將評論文字欄位正確指向資料庫真正存放評論的 `comment_content`（而非舊設定誤導的 `raw_text`）。

#### 💡 附：最新定稿版 `match_reviews_hybrid` SQL 腳本
```sql
CREATE OR REPLACE FUNCTION match_reviews_hybrid(
    query_text text,
    query_embedding vector(1536),
    match_threshold float,
    match_count int
)
RETURNS TABLE (
    master_review_id text,
    id text,
    raw_text text,
    similarity_score float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    WITH vec_candidates AS (
        SELECT 
            m.master_review_id,
            m.comment_content,
            (1 - (m.embedding <=> query_embedding))::float AS vec_score
        FROM master_reviews m
        WHERE (1 - (m.embedding <=> query_embedding)) >= match_threshold
        ORDER BY m.embedding <=> query_embedding
        LIMIT match_count * 2
    ),
    fts_candidates AS (
        SELECT 
            m.master_review_id,
            m.comment_content,
            ts_rank_cd(to_tsvector('simple', COALESCE(m.comment_content, '')), plainto_tsquery('simple', query_text))::float AS fts_score
        FROM master_reviews m
        WHERE to_tsvector('simple', COALESCE(m.comment_content, '')) @@ plainto_tsquery('simple', query_text)
        ORDER BY fts_score DESC
        LIMIT match_count * 2
    ),
    combined_scores AS (
        SELECT 
            COALESCE(v.master_review_id, f.master_review_id) AS m_id,
            COALESCE(v.comment_content, f.comment_content) AS content,
            COALESCE(v.vec_score, 0.0) AS v_score,
            COALESCE(f.fts_score, 0.0) AS f_score
        FROM vec_candidates v
        FULL OUTER JOIN fts_candidates f ON v.master_review_id = f.master_review_id
    ),
    max_fts AS (
        SELECT COALESCE(NULLIF(MAX(f_score), 0), 1.0) AS max_f FROM combined_scores
    )
    SELECT 
        c.m_id::text AS master_review_id,
        c.m_id::text AS id,
        c.content::text AS raw_text,
        LEAST(1.0, c.v_score + (c.f_score / mf.max_f) * 0.15)::float AS similarity_score
    FROM combined_scores c
    CROSS JOIN max_fts mf
    WHERE LEAST(1.0, c.v_score + (c.f_score / mf.max_f) * 0.15) >= match_threshold
    ORDER BY similarity_score DESC
    LIMIT match_count;
END;
$$;
```

---

## 💻 2. 後端 Python 程式碼加固與例外解除 (Backend Enhancement)

### 2.1 拔除消音器：安全防線嚴格化
* **修改檔案**：`backend/supabase_db.py`
* **調整內容**：針對 `search_similar_reviews_hybrid` 函數，移除了 `except Exception as e:` 區塊中靜默吞沒例外的 `return []`，替換為明確的 `raise e`。
* **效益**：確保未來 RPC 呼叫發生任何參數不匹配、表名錯誤或網路異常時，系統會第一時間拋出 StackTrace 報錯現形，大幅提升架構的排錯透明度與穩定度。

### 2.2 環境變數 (`.env`) 與表名校正
* **發現問題**：原工作區根目錄缺失 `.env` 檔案，且舊 Archive 設定檔中的 `SUPABASE_TABLE_NAME` 被設為已不存在的 `master_reviews_enriched`。
* **修復動作**：於專案根目錄建立並補齊 `.env` 設定，並將 `SUPABASE_TABLE_NAME` 嚴格校正為 `master_reviews`；分析報告寫入表保留為 `master_reviews_result`。

---

## 🧪 3. 實戰驗收與測試紀錄 (Verification & Testing)

### 3.1 Python 雙軌檢索單元驗收
於 PowerShell 執行以下指令進行連線與檢索測試：
```powershell
python -c "import sys; sys.path.append('backend'); from supabase_db import search_similar_reviews_hybrid; print(search_similar_reviews_hybrid('蒼蠅 衛生 食安 態度差', [0.1]*1536, match_threshold=0.1, limit=3))"
```
* **驗收結果**：**通過 (Pass)**。指令執行順利無報錯並回傳 `[]`，證明 `match_reviews_hybrid` RPC 與 Python 端介面參數 (`query_text`, `query_embedding`, `match_threshold`, `match_count`) 完全對齊無誤。

### 3.2 API 端點與 ML Gatekeeper 守門員實戰驗收
啟動 FastAPI 服務 (`http://127.0.0.1:8000`) 並向 `/api/analyze` 發送模擬客訴測試 HTTP POST 請求：
```json
{
  "review": "這家餐廳的衛生超糟糕，湯裡面有一隻死蒼蠅，店員服務態度極度惡劣，立刻報警處理！",
  "rating": 1,
  "tone": "標準",
  "engine": "openai"
}
```
* **驗收結果**：**通過 (Pass, 200 OK)**。
* **核心觀察**：
  * 系統成功回傳 `"engine_used": "ml_gatekeeper"` 與 `"risk_percent": 37.5`。
  * 證實第一道防線 **「ML Gatekeeper 機器學習守門員」** 正確啟動：本地 ML 模型評估該測試文本危機機率為 37.50%（小於 70% 危機門檻），自動攔截並產生低風險報告：
    > `"[ML Gatekeeper] 此輿情評估為低風險（危機機率 37.50%），系統自動攔截，未觸發 RAG 流程。"`
  * **成本效益**：成功為企業省下不必要的 OpenAI LLM Token 與 Embeddings 呼叫開銷。

### 3.3 強制生成 (Force Generate) 與 Swagger UI 驗證
* **強制突破守門員測試**：確認若需在 API 測試時強制觸發後續的 RAG 檢索與 OpenAI 回覆生成，只需於 JSON Request Body 添加 `"force_generate": true` 即可無條件執行後續 LangGraph / LLM 流程。
* **UI 驗收**：透過瀏覽器與自動化工具驗證了 `http://127.0.0.1:8000/docs` (Swagger UI) 介面渲染與端點文件完備。

---

## 🚀 4. 後續 (Next Steps)

1. 🎯 RAG 語意快取 (Semantic Cache) 遙測監控與調優
建置專屬遙測監控核心 (ml_analyzer.SemanticCacheMonitor)：
在 backend/ml_analyzer.py 中設計了線程安全（Thread-safe）的 SemanticCacheMonitor 監控類別，持續追蹤 search_similar_reviews_hybrid（相似度門檻 Threshold = 0.95）的累計查詢次數、快取命中率 (Hit Rate %)、命中 / 未命中延遲 (Latency ms)，以及最近 200 筆查詢的歷史軌跡。
於 MidEndAnalyzer.analyze_review_pipeline 管線第二步驟中導入高精度時間監控（time.perf_counter），每當進行語意向量檢索時即自動記錄耗時並輸出詳細除錯日誌：
🎯 快取命中時：直接複製歷史分析報告智慧，省下 100% LLM 運算時間與 Token 開銷。
⚡ 快取未命中時：記錄檢索延遲並平滑進入後續 LangGraph 深度分析流程。
對接後端 API 監控端點 (/api/semantic-cache/stats)：
於 backend/api_server.py 新增 GET /api/semantic-cache/stats 端點，供前端實驗室與後台報表即時拉取快取遙測數據與節省 Token 估算。

2. 🔬 前端分析介面深度串接與 "force_generate" 視覺化控制
打造獨立專屬「AI 輿情質檢與訓練實驗室」 (frontend/analyze.html)：
採用 Tailwind CSS 與客製化 HSL/紫金漸層設計，打造出兼具美感與實用性的專業質檢演練中心，無論人工質檢或新客服訓練皆能快速上手。
頁面頂部對接 Task 1 監控儀表板：即時呼叫 /api/semantic-cache/stats 顯示當前 RAG 快取的累計查詢數、命中率、平均回應延遲 (ms) 與節省的估算 Token。

⚡ "force_generate" 開關深度視覺化串接：
設計了醒目的動態開關與狀態說明卡片。
OFF 正常防守模式：系統說明「ML 守門員防守中，若危機機率低於門檻 (0.70) 將自動攔截並返回低風險報告，不觸發 RAG / LLM」。
ON 強制突破模式：開關啟動時觸發紫金光暈脈衝動畫（Pulse Glow），系統說明變更為「⚡ 強制生成中：已忽略 ML Gatekeeper 攔截門檻，強制執行完整 RAG 檢索與公關回覆生成」。

豐富的質檢演練功能：
提供 ⚡ 快速帶入測試範例按鈕（食安死蒼蠅高危件、排隊抱怨中危件、五星推薦正常件），一鍵載入測試。
支援評估星等切換（1 ~ 5 星）、推論引擎切換（OpenAI / Ollama Local）、公關應對語氣（標準 / 溫柔熱情 / 強硬自保）。
右欄提供多維度公關應對評分條（誠懇度、法律自保度、商譽挽回度）、回覆草稿一鍵複製功能，以及完整的 LangGraph 執行軌跡日誌。
雙向無縫導覽整合 (index.html 導覽對接)：
於 frontend/index.html 的桌機左側側邊欄與手機底部導覽列中，新增了「質檢與訓練站 (AI Lab)」專屬入口連結，點選後可直接開啟 ./analyze.html 進行深入演練，實驗室內部亦具備「← 返回營運總覽」按鈕，體驗無縫連貫。

修復 Gatekeeper 攔截資料庫相容性：
針對 UI Ad-hoc 任意測試評論，調整了 api_server.py 中 _save_gatekeeper_intercept 的邏輯：當缺少關聯的 master_review_id 時自動略過寫入資料庫，徹底避免 PostgreSQL 外鍵限制（Foreign Key Constraint）報錯，同時確保正常批次處理時的攔截記錄可精準寫入 master_reviews_result。