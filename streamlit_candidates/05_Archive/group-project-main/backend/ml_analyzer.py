import streamlit as st
st.title('ml_analyzer.py - 自動化展示')
st.info('這是從原專案腳本自動包裝產生的互動式介面。')

"""
ml_analyzer.py
─────────────────────────────────────────────────────────────────────────────
中端核心分析器（企業級防禦與多維賦能版）

功能：
  1. 語意快取防線：新評論傳入時，先檢索是否有極度相似的歷史分析，實現秒級響應。
  2. 多維情感解構：產出 joy / anger / disappointment 數值，豐富前端圖表血肉。
  3. 自動範疇打標：生成 reviews_tag，為前端提供靈活的動態篩選器。
  4. 自動持久化：分析完成後自動調用 upsert 寫入結果表。
─────────────────────────────────────────────────────────────────────────────
"""

import os
import time
import datetime
import logging
import threading
from supabase_db import search_similar_reviews_hybrid, upsert_ml_analysis_result

log = logging.getLogger(__name__)

class SemanticCacheMonitor:
    """
    語意快取遙測監控器 (Semantic Cache Telemetry Monitor)
    持續監控 RAG 語意快取 (Threshold = 0.95) 的命中率、查詢次數與回應延遲 (Latency)
    """
    def __init__(self, threshold: float = 0.95, max_history: int = 200):
        self.threshold = threshold
        self.max_history = max_history
        self._lock = threading.Lock()
        self.total_queries = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.total_latency_ms = 0.0
        self.hit_latency_ms = 0.0
        self.miss_latency_ms = 0.0
        self.history: list[dict] = []

    def record_query(self, query_text: str, is_hit: bool, latency_ms: float, hit_data: dict | None = None) -> dict:
        with self._lock:
            self.total_queries += 1
            self.total_latency_ms += latency_ms
            if is_hit:
                self.cache_hits += 1
                self.hit_latency_ms += latency_ms
            else:
                self.cache_misses += 1
                self.miss_latency_ms += latency_ms
            
            hit_rate = (self.cache_hits / self.total_queries) if self.total_queries > 0 else 0.0
            avg_latency = (self.total_latency_ms / self.total_queries) if self.total_queries > 0 else 0.0
            
            log_entry = {
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "query_snippet": query_text[:50] + ("..." if len(query_text) > 50 else ""),
                "is_hit": is_hit,
                "latency_ms": round(latency_ms, 2),
                "hit_rate_current": round(hit_rate, 4),
                "threshold": self.threshold
            }
            if hit_data and isinstance(hit_data, dict) and "similarity" in hit_data:
                log_entry["similarity"] = hit_data.get("similarity")
            
            self.history.append(log_entry)
            if len(self.history) > self.max_history:
                self.history.pop(0)
                
            return {
                "hit_rate": hit_rate,
                "avg_latency_ms": avg_latency,
                "latency_ms": latency_ms,
                "total_queries": self.total_queries,
                "cache_hits": self.cache_hits,
                "cache_misses": self.cache_misses
            }

    def get_stats(self) -> dict:
        with self._lock:
            hit_rate = (self.cache_hits / self.total_queries) if self.total_queries > 0 else 0.0
            avg_latency = (self.total_latency_ms / self.total_queries) if self.total_queries > 0 else 0.0
            avg_hit_latency = (self.hit_latency_ms / self.cache_hits) if self.cache_hits > 0 else 0.0
            avg_miss_latency = (self.miss_latency_ms / self.cache_misses) if self.cache_misses > 0 else 0.0
            return {
                "threshold": self.threshold,
                "total_queries": self.total_queries,
                "cache_hits": self.cache_hits,
                "cache_misses": self.cache_misses,
                "hit_rate": round(hit_rate, 4),
                "hit_rate_percent": f"{hit_rate * 100:.2f}%",
                "avg_latency_ms": round(avg_latency, 2),
                "avg_hit_latency_ms": round(avg_hit_latency, 2),
                "avg_miss_latency_ms": round(avg_miss_latency, 2),
                "recent_history": list(reversed(self.history[-20:]))
            }

    def reset(self):
        with self._lock:
            self.total_queries = 0
            self.cache_hits = 0
            self.cache_misses = 0
            self.total_latency_ms = 0.0
            self.hit_latency_ms = 0.0
            self.miss_latency_ms = 0.0
            self.history.clear()

# 模組層級單例監控器，供中端管線與外部 API 共同存取與監控
cache_monitor = SemanticCacheMonitor(threshold=0.95)

def get_semantic_cache_telemetry() -> dict:
    """獲取語意快取目前的即時遙測數據 (供 API 與後台報表調用)"""
    return cache_monitor.get_stats()


class MidEndAnalyzer:
    def __init__(self, llm_client=None, embedding_client=None):
        self.llm = llm_client
        self.embedding_client = embedding_client

    def get_cache_stats(self) -> dict:
        """獲取該分析器對應之語意快取遙測數據"""
        return cache_monitor.get_stats()

    def analyze_review_pipeline(self, source_record: dict, dry_run: bool = False) -> dict:
        """
        中端複合分析管線 —— 兼顧後端防禦與前端視覺
        """
        comment_content = source_record.get("comment_content", "").strip()
        rating = source_record.get("rating", 3)
        
        if not comment_content:
            return {"status": "error", "message": "評論內容不可為空"}

        # ── 核心步驟一：生成當前評論之向量座標 ──
        query_vector = None
        if self.embedding_client:
            try:
                query_vector = self.embedding_client.embed_query(comment_content)
            except Exception as e:
                log.warning(f"[Embedding 失敗]: {e}")

        # ── 核心步驟二：語意快取防線 (Semantic Cache 監控調優版) ──
        if query_vector:
            start_time = time.perf_counter()
            cached_hits = search_similar_reviews_hybrid(
                query_text=comment_content,
                query_vector=query_vector,
                match_threshold=0.95,
                limit=1
            )
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            
            if cached_hits:
                hit_cache = cached_hits[0]
                stats = cache_monitor.record_query(comment_content, is_hit=True, latency_ms=latency_ms, hit_data=hit_cache)
                log.info(
                    f"🎯 [語意快取命中]！相似度門檻 Threshold=0.95 | "
                    f"回應延遲: {latency_ms:.2f}ms | 累計命中率: {stats['hit_rate']:.2%} ({stats['cache_hits']}/{stats['total_queries']}) | "
                    f"直接複製歷史智慧，免除 LLM 運算開銷。"
                )
                return {"status": "cache_hit", "data": hit_cache, "cache_telemetry": stats}
            else:
                stats = cache_monitor.record_query(comment_content, is_hit=False, latency_ms=latency_ms)
                log.info(
                    f"⚡ [語意快取未命中] 進入後續 LLM 分析 | "
                    f"檢索延遲: {latency_ms:.2f}ms | 累計命中率: {stats['hit_rate']:.2%} ({stats['cache_hits']}/{stats['total_queries']})"
                )

        # ── 核心步驟三：LLM 深度多維解構 (對齊前後端需求) ──
        analysis_row = {
            "sentiment_label": "neutral",
            "sentiment_score": 0.5,
            "risk_score": 0.0,
            "risk_level": "正常無虞",
            "emotion_joy": 10,
            "emotion_anger": 10,
            "emotion_disappointment": 10,
            "reviews_tag": "一般意見",
            "is_meaningful": True,
            "content_type": "未分類",
            "content_quality_score": 60,
            "filter_reason": None,
            "analyzed_at": datetime.datetime.utcnow().isoformat()
        }

        if self.llm:
            prompt = f"""請分析以下評論，並嚴格依據結構化格式回報。
            
            評論內容：\"{comment_content}\"
            
            請評估以下維度（分數皆為 0 到 100 的整數）：
            1. 喜悅值 (joy)
            2. 憤怒值 (anger)
            3. 失望值 (disappointment)
            4. 危機風險分數 (risk_score)
            5. 分類範疇標籤 (tag)：只能從 [食安問題, 服務態度, 環境髒亂, 消費糾紛, 一般好評] 挑選一個最合適的。
            
            回覆格式範例（嚴禁任何其他贅字）：
            anger:85|disappointment:90|joy:0|risk_score:95|tag:食安問題
            """
            try:
                response = self.llm.invoke(prompt)
                raw_res = response.content.strip()
                
                parts = dict(item.split(":") for item in raw_res.split("|") if ":" in item)
                
                analysis_row["emotion_anger"] = int(parts.get("anger", 10))
                analysis_row["emotion_disappointment"] = int(parts.get("disappointment", 10))
                analysis_row["emotion_joy"] = int(parts.get("joy", 10))
                analysis_row["risk_score"] = float(parts.get("risk_score", 0)) / 100.0
                analysis_row["reviews_tag"] = parts.get("tag", "一般意見").strip()
                
                if analysis_row["risk_score"] >= 0.75:
                    analysis_row["risk_level"] = "高度危機"
                    analysis_row["sentiment_label"] = "negative"
                elif analysis_row["risk_score"] >= 0.40:
                    analysis_row["risk_level"] = "中度風險"
                    analysis_row["sentiment_label"] = "negative"
                else:
                    analysis_row["risk_level"] = "正常無虞"
                    analysis_row["sentiment_label"] = "positive" if analysis_row["emotion_joy"] > 50 else "neutral"
                    
            except Exception as lexc:
                log.error(f"[LLM 多維分析失敗]，啟用安全備用數據。原因: {lexc}")

        # ── 核心步驟四：落實自動持久化 ──
        if not dry_run:
            db_res = upsert_ml_analysis_result(source_record, analysis_row)
            return {"status": "processed", "db_result": db_res, "analysis": analysis_row}
        
        return {"status": "dry_run", "analysis": analysis_row}


if __name__ == "__main__":
    import sys
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    st.write("=" * 60)
    st.write("🧪 啟動 RAG 語意快取 (Semantic Cache, Threshold=0.95) 監控驗收")
    st.write("=" * 60)
    
    # 模擬向量客戶端
    class MockEmbeddingClient:
        def embed_query(self, text):
            # 產生模擬向量
            return [0.1] * 1536

    analyzer = MidEndAnalyzer(embedding_client=MockEmbeddingClient())
    
    test_reviews = [
        {"comment_content": "湯裡面有蒼蠅，衛生環境超級差，服務態度惡劣！", "rating": 1},
        {"comment_content": "這家熱炒店的牛肉很嫩，啤酒很冰，推！", "rating": 5},
        {"comment_content": "湯裡面有蒼蠅，衛生環境超級差，服務態度惡劣！", "rating": 1}, # 測試命中
        {"comment_content": "上菜超慢，點了兩小時才來一盤菜，餓死了。", "rating": 1},
    ]
    
    for i, rev in enumerate(test_reviews, 1):
        st.write(f"\n[測試案例 #{i}] 評論內容: \"{rev['comment_content']}\"")
        res = analyzer.analyze_review_pipeline(rev, dry_run=True)
        st.write(f" -> 處理狀態: {res.get('status')}")
    
    st.write("\n📊 語意快取遙測數據總覽 (Telemetry Stats):")
    import json
    st.write(json.dumps(analyzer.get_cache_stats(), indent=2, ensure_ascii=False))
    st.write("=" * 60)