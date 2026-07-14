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
import datetime
import logging
from supabase_db import search_similar_reviews_hybrid, upsert_ml_analysis_result

log = logging.getLogger(__name__)

class MidEndAnalyzer:
    def __init__(self, llm_client=None, embedding_client=None):
        self.llm = llm_client
        self.embedding_client = embedding_client

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

        # ── 核心步驟二：語意快取防線 (Semantic Cache) ──
        if query_vector:
            cached_hits = search_similar_reviews_hybrid(
                query_text=comment_content,
                query_vector=query_vector,
                match_threshold=0.95,
                limit=1
            )
            if cached_hits:
                log.info("🎯 [語意快取命中]！直接複製歷史分析智慧，免除 LLM 開銷。")
                hit_cache = cached_hits[0]
                return {"status": "cache_hit", "data": hit_cache}

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