import streamlit as st
st.title('supabase_db.py - 自動化展示')
st.info('這是從原專案腳本自動包裝產生的互動式介面。')

import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables from the project root even when scripts run from subfolders.
BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")

def _env_value(name: str) -> str:
    value = (os.environ.get(name) or "").strip()
    if not value or value.startswith("your-"):
        return ""
    return value


# Initialize Supabase client
SUPABASE_URL = _env_value("SUPABASE_URL")
SUPABASE_ANON_KEY = _env_value("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_ROLE_KEY = _env_value("SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_KEY = SUPABASE_SERVICE_ROLE_KEY or _env_value("SUPABASE_KEY") or SUPABASE_ANON_KEY

SUPABASE_TABLE_NAME = os.environ.get("SUPABASE_TABLE_NAME", "master_reviews")
SUPABASE_RESULT_TABLE_NAME = os.environ.get("SUPABASE_RESULT_TABLE_NAME", "master_reviews_result")

SOURCE_REVIEW_SELECT = ",".join([
    "master_review_id",
    "business_id",
    "business_name",
    "platform",
    "posts_id",
    "post_published_at",
    "post_title",
    "post_author_id",
    "post_author_name",
    "comment_author_id",
    "comment_author_name",
    "comment_content",
    "comment_published_at",
])

DASHBOARD_RESULT_SELECT = ",".join([
    "master_review_id",
    "business_id",
    "business_name",
    "platform",
    "posts_id",
    "post_published_at",
    "post_title",
    "post_author_id",
    "post_author_name",
    "comment_author_id",
    "comment_author_name",
    "comment_content",
    "comment_published_at",
    "sentiment_label",
    "sentiment_score",
    "risk_score",
    "risk_level",
    "emotion_joy",
    "emotion_anger",
    "emotion_disappointment",
    "reviews_tag",
    "analyzed_at",
    "is_meaningful",
    "content_type",
    "content_quality_score",
    "filter_reason",
    "reviews_response",
    "status",
    "created_at",
    "updated_at",
])

if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        st.write(f"[Warning] Failed to initialize Supabase client: {e}")
        supabase = None
else:
    supabase = None
    st.write("[Info] SUPABASE_URL and a Supabase key are required.")


def init_dynamic_client(url: str, key: str, table_name: str = "master_reviews"):
    global supabase, SUPABASE_TABLE_NAME
    if url and key:
        try:
            supabase = create_client(url, key)
            SUPABASE_TABLE_NAME = table_name
            return True
        except Exception as e:
            st.write(f"[Warning] Failed to initialize dynamic client: {e}")
    return False


def save_pr_report(review: str, rating: int, sentiment: str, risk_percent: float, report_content: str, engine: str, embedding=None):
    if not supabase:
        return {"status": "error", "message": "Supabase client not initialized"}
    
    try:
        raw_data = {
            "raw_text": review,
            "rating": int(rating) if rating is not None else None,
            "sentiment": sentiment,
            "sentiment_label": sentiment,
            "risk_percent": float(risk_percent) if risk_percent is not None else None,
            "report_content": report_content,
            "engine": engine,
            "embedding": embedding
        }
        
        try:
            candidate_cols = ",".join(raw_data.keys())
            sample = supabase.table(SUPABASE_TABLE_NAME).select(candidate_cols).limit(1).execute()
            if sample.data and len(sample.data) > 0:
                cols = set(sample.data[0].keys())
                data = {k: v for k, v in raw_data.items() if k in cols}
            else:
                if SUPABASE_TABLE_NAME in ("review", "reviews_enriched", "master_reviews_enriched", "master_reviews"):
                    cols = {"review_id", "reviewer", "review_time", "raw_text", "rating", "platform", "sentiment", "sentiment_label", "risk_percent", "report_content", "engine"}
                    data = {k: v for k, v in raw_data.items() if k in cols}
                else:
                    data = raw_data
        except Exception as e_schema:
            st.write(f"[Warning] Failed to fetch table schema, using default insert: {e_schema}")
            data = raw_data

        data = {k: v for k, v in data.items() if v is not None}
        response = supabase.table(SUPABASE_TABLE_NAME).insert(data).execute()
        return {"status": "success", "data": response.data}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def search_similar_reviews(query_vector, rating, match_threshold=0.75, limit=3):
    """傳統向量相似度檢索"""
    if not supabase:
        return []
    try:
        response = supabase.rpc(
            "match_reviews",
            {
                "query_embedding": query_vector,
                "match_threshold": match_threshold,
                "match_count": limit,
                "filter_rating": int(rating)
            }
        ).execute()
        return response.data if response.data else []
    except Exception as e:
        st.write(f"[Warning] Supabase match_reviews RPC failed: {e}")
        return []


def search_similar_reviews_hybrid(query_text, query_vector, match_threshold=0.70, limit=3):
    """
    🎯【企業級優化核心】：呼叫 Supabase 進行關鍵字(BM25) + 向量(Embedding) 的 Hybrid 混合檢索
    """
    if not supabase:
        return []
    try:
        response = supabase.rpc(
            "match_reviews_hybrid",
            {
                "query_text": query_text,
                "query_embedding": query_vector,
                "match_threshold": match_threshold,
                "match_count": limit
            }
        ).execute()
        return response.data if response.data else []
    except Exception as e:
        st.write(f"[Warning] Supabase match_reviews_hybrid RPC failed: {e}")
        raise e


def _apply_order(query, order: str | None):
    if not order:
        return query
    parts = [part for part in str(order).split(".") if part]
    if not parts:
        return query
    column = parts[0]
    desc = "desc" in parts[1:]
    nullsfirst = "nullsfirst" in parts[1:]
    try:
        return query.order(column, desc=desc, nullsfirst=nullsfirst)
    except TypeError:
        return query.order(column, desc=desc)


def _fetch_table_batches(
    table_name: str,
    columns: str = "*",
    batch_size: int = 1000,
    limit: int | None = None,
    order: str | None = None,
    filters: dict | None = None,
):
    if not supabase:
        return []
    data: list[dict] = []
    start = 0
    batch_size = max(1, min(int(batch_size or 1000), 1000))
    max_rows = None if limit is None or limit <= 0 else int(limit)

    while True:
        requested = batch_size if max_rows is None else min(batch_size, max_rows - len(data))
        if requested <= 0:
            break
        end = start + requested - 1
        query = supabase.table(table_name).select(columns or "*")
        for key, value in (filters or {}).items():
            if value is not None and value != "":
                query = query.eq(key, value)
        response = _apply_order(query, order).range(start, end).execute()
        batch = response.data or []
        data.extend(batch)
        if len(batch) < requested:
            break
        start += requested
    return data


def fetch_all_reports(
    batch_size: int = 1000,
    limit: int | None = None,
    columns: str = SOURCE_REVIEW_SELECT,
    order: str = "comment_published_at.desc.nullslast",
):
    if not supabase:
        return []
    try:
        try:
            data = _fetch_table_batches(SUPABASE_TABLE_NAME, columns, batch_size=batch_size, limit=limit, order=order)
        except Exception:
            if columns == "*":
                raise
            data = _fetch_table_batches(SUPABASE_TABLE_NAME, "*", batch_size=batch_size, limit=limit, order=order)

        if data and isinstance(data, list) and len(data) > 0:
            if "created_at" in data[0]:
                try: data = sorted(data, key=lambda x: x.get("created_at", ""), reverse=True)
                except Exception: pass
            elif "comment_content" in data[0] or "comment_published_at" in data[0]:
                try: data = sorted(data, key=lambda x: x.get("comment_published_at", ""), reverse=True)
                except Exception: pass
        return data
    except Exception as e:
        st.write(f"[Warning] Failed to fetch reports from Supabase: {e}")
        raise e


def fetch_existing_result_ids(batch_size: int = 1000) -> set:
    if not supabase:
        return set()
    try:
        ids = set()
        start = 0
        batch_size = max(1, min(int(batch_size or 1000), 1000))

        while True:
            end = start + batch_size - 1
            response = (
                supabase.table(SUPABASE_RESULT_TABLE_NAME)
                .select("master_review_id,content_type")
                .range(start, end)
                .execute()
            )
            batch = response.data or []
            for row in batch:
                value = row.get("master_review_id")
                if value is not None and row.get("content_type"):
                    ids.add(value)
            if len(batch) < batch_size:
                break
            start += batch_size
        return ids
    except Exception as e:
        st.write(f"[Warning] Failed to fetch existing result ids: {e}")
        raise e


def fetch_result_reports(
    batch_size: int = 1000,
    limit: int | None = None,
    columns: str = DASHBOARD_RESULT_SELECT,
    order: str = "comment_published_at.desc.nullslast",
    business_name: str = "",
):
    if not supabase:
        return []
    try:
        try:
            filters = {"business_name": business_name} if business_name else None
            return _fetch_table_batches(SUPABASE_RESULT_TABLE_NAME, columns, batch_size=batch_size, limit=limit, order=order, filters=filters)
        except Exception:
            if columns == "*":
                raise
            filters = {"business_name": business_name} if business_name else None
            return _fetch_table_batches(SUPABASE_RESULT_TABLE_NAME, "*", batch_size=batch_size, limit=limit, order=order, filters=filters)
    except Exception as e:
        st.write(f"[Warning] Failed to fetch result reports from Supabase: {e}")
        raise e


def clear_ml_analysis_results(batch_size: int = 1000):
    """Delete every keyed row from the dashboard result table."""
    if not supabase:
        return {"status": "error", "message": "Supabase client not initialized", "deleted": 0}

    try:
        result_ids = list(fetch_existing_result_ids(batch_size=batch_size))
        for offset in range(0, len(result_ids), batch_size):
            batch_ids = result_ids[offset:offset + batch_size]
            (
                supabase.table(SUPABASE_RESULT_TABLE_NAME)
                .delete()
                .in_("master_review_id", batch_ids)
                .execute()
            )
        return {"status": "success", "deleted": len(result_ids)}
    except Exception as e:
        return {"status": "error", "message": str(e), "deleted": 0}


def upsert_ml_analysis_result(source_record: dict, analysis_row: dict, dry_run: bool = False):
    if not supabase:
        return {"status": "error", "message": "Supabase client not initialized"}

    master_review_id = (
        source_record.get("master_review_id")
        or analysis_row.get("master_review_id")
        or source_record.get("review_id")
        or source_record.get("id")
    )
    if master_review_id is None:
        return {"status": "skipped", "message": "No valid key available for result upsert"}

    result_data = {
        "master_review_id": master_review_id,
        "business_id": source_record.get("business_id"),
        "business_name": source_record.get("business_name"),
        "platform": source_record.get("platform"),
        "posts_id": source_record.get("posts_id"),
        "post_published_at": source_record.get("post_published_at"),
        "post_title": source_record.get("post_title"),
        "post_author_id": source_record.get("post_author_id"),
        "post_author_name": source_record.get("post_author_name"),
        "comment_author_id": source_record.get("comment_author_id"),
        "comment_author_name": source_record.get("comment_author_name"),
        "comment_content": source_record.get("comment_content"),
        "comment_published_at": source_record.get("comment_published_at"),

        "sentiment_label": analysis_row.get("sentiment_label"),
        "sentiment_score": analysis_row.get("sentiment_score"),
        "risk_score": analysis_row.get("risk_score"),
        "risk_level": analysis_row.get("risk_level"),
        "emotion_joy": analysis_row.get("emotion_joy"),
        "emotion_anger": analysis_row.get("emotion_anger"),
        "emotion_disappointment": analysis_row.get("emotion_disappointment"),
        "reviews_tag": analysis_row.get("reviews_tag"),
        "analyzed_at": analysis_row.get("analyzed_at"),
        "is_meaningful": analysis_row.get("is_meaningful"),
        "content_type": analysis_row.get("content_type"),
        "content_quality_score": analysis_row.get("content_quality_score"),
        "filter_reason": analysis_row.get("filter_reason"),
    }
    result_data = {key: value for key, value in result_data.items() if value is not None}

    if dry_run:
        return {"status": "dry_run", "table": SUPABASE_RESULT_TABLE_NAME, "master_review_id": master_review_id}

    try:
        response = (
            supabase.table(SUPABASE_RESULT_TABLE_NAME)
            .upsert(result_data, on_conflict="master_review_id")
            .execute()
        )
        return {"status": "success", "data": response.data}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def update_ml_analysis_fields(source_record: dict, analysis_row: dict, dry_run: bool = False):
    return upsert_ml_analysis_result(source_record, analysis_row, dry_run=dry_run)


# ====== 自動生成的測試執行區塊 ======
if __name__ == "__main__":
    st.write("---")
    st.subheader("函數測試區塊")
    if st.button("執行 init_dynamic_client"):
        try:
            res = init_dynamic_client() # 請視需要自行補上參數
            st.write("執行結果:", res)
        except Exception as e:
            st.error(f"執行出錯，可能需要提供參數：{e}")
    if st.button("執行 save_pr_report"):
        try:
            res = save_pr_report() # 請視需要自行補上參數
            st.write("執行結果:", res)
        except Exception as e:
            st.error(f"執行出錯，可能需要提供參數：{e}")
    if st.button("執行 search_similar_reviews"):
        try:
            res = search_similar_reviews() # 請視需要自行補上參數
            st.write("執行結果:", res)
        except Exception as e:
            st.error(f"執行出錯，可能需要提供參數：{e}")
    if st.button("執行 search_similar_reviews_hybrid"):
        try:
            res = search_similar_reviews_hybrid() # 請視需要自行補上參數
            st.write("執行結果:", res)
        except Exception as e:
            st.error(f"執行出錯，可能需要提供參數：{e}")
    if st.button("執行 fetch_all_reports"):
        try:
            res = fetch_all_reports() # 請視需要自行補上參數
            st.write("執行結果:", res)
        except Exception as e:
            st.error(f"執行出錯，可能需要提供參數：{e}")
    if st.button("執行 fetch_existing_result_ids"):
        try:
            res = fetch_existing_result_ids() # 請視需要自行補上參數
            st.write("執行結果:", res)
        except Exception as e:
            st.error(f"執行出錯，可能需要提供參數：{e}")
    if st.button("執行 fetch_result_reports"):
        try:
            res = fetch_result_reports() # 請視需要自行補上參數
            st.write("執行結果:", res)
        except Exception as e:
            st.error(f"執行出錯，可能需要提供參數：{e}")
    if st.button("執行 clear_ml_analysis_results"):
        try:
            res = clear_ml_analysis_results() # 請視需要自行補上參數
            st.write("執行結果:", res)
        except Exception as e:
            st.error(f"執行出錯，可能需要提供參數：{e}")
    if st.button("執行 upsert_ml_analysis_result"):
        try:
            res = upsert_ml_analysis_result() # 請視需要自行補上參數
            st.write("執行結果:", res)
        except Exception as e:
            st.error(f"執行出錯，可能需要提供參數：{e}")
    if st.button("執行 update_ml_analysis_fields"):
        try:
            res = update_ml_analysis_fields() # 請視需要自行補上參數
            st.write("執行結果:", res)
        except Exception as e:
            st.error(f"執行出錯，可能需要提供參數：{e}")
