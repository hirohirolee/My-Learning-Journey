import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Initialize Supabase client
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
SUPABASE_TABLE_NAME = os.environ.get("SUPABASE_TABLE_NAME", "reviews")

if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"[Warning] Failed to initialize Supabase client: {e}")
        supabase = None
else:
    supabase = None
    print("[Info] SUPABASE_URL or SUPABASE_KEY not set. Supabase operations will be skipped.")

def init_dynamic_client(url: str, key: str, table_name: str = "reviews"):
    """
    Dynamically re-initializes the Supabase client with custom credentials.
    """
    global supabase, SUPABASE_TABLE_NAME
    if url and key:
        try:
            supabase = create_client(url, key)
            SUPABASE_TABLE_NAME = table_name
            return True
        except Exception as e:
            print(f"[Warning] Failed to initialize dynamic client: {e}")
    return False


def save_pr_report(review: str, rating: int, sentiment: str, risk_percent: float, report_content: str, engine: str, embedding=None):
    """
    Saves the review and analysis results into the Supabase database.
    """
    if not supabase:
        return {"status": "error", "message": "Supabase client not initialized"}
    
    try:
        # 準備資料字典，並同時寫入預設欄位與使用者自訂欄位 (如 sentiment_label)
        raw_data = {
            "review": review,
            "rating": rating,
            "sentiment": sentiment,
            "sentiment_label": sentiment,  # 對應使用者的 review 表欄位
            "risk_percent": float(risk_percent) if risk_percent is not None else None,
            "report_content": report_content,
            "engine": engine,
            "embedding": embedding
        }
        
        # 嘗試動態偵測資料表包含哪些欄位，防止因多餘欄位導致寫入失敗
        try:
            sample = supabase.table(SUPABASE_TABLE_NAME).select("*").limit(1).execute()
            if sample.data and len(sample.data) > 0:
                cols = set(sample.data[0].keys())
                data = {k: v for k, v in raw_data.items() if k in cols}
            else:
                # 若為空表且表名為 review，使用剛才在 Schema 看到的實體欄位過濾
                if SUPABASE_TABLE_NAME == "review":
                    cols = {"id", "business_id", "rating", "review_type", "sentiment_label", "published_at", "crawled_at", "embedding", "report_content"}
                    data = {k: v for k, v in raw_data.items() if k in cols}
                else:
                    data = raw_data
        except Exception as e_schema:
            print(f"[Warning] Failed to fetch table schema, using default insert: {e_schema}")
            data = raw_data
            
        response = supabase.table(SUPABASE_TABLE_NAME).insert(data).execute()
        return {"status": "success", "data": response.data}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def search_similar_reviews(query_vector, rating, match_threshold=0.6, limit=2):
    """
    呼叫 Supabase SQL RPC (match_reviews) 進行向量相似度檢索，限制相同評分以保證情境一致
    """
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
        print(f"[Warning] Supabase match_reviews RPC failed: {e}")
        return []


def fetch_all_reports():
    """
    Fetches all historical reports from Supabase.
    """
    if not supabase:
        return []
    try:
        response = supabase.table(SUPABASE_TABLE_NAME).select("*").execute()
        data = response.data
        if data and isinstance(data, list) and len(data) > 0:
            # 優先嘗試以 created_at 進行排序
            if "created_at" in data[0]:
                try:
                    data = sorted(data, key=lambda x: x.get("created_at", ""), reverse=True)
                except:
                    pass
            # 如果沒有 created_at 但有 id，則以 id 排序
            elif "id" in data[0]:
                try:
                    data = sorted(data, key=lambda x: x.get("id", 0), reverse=True)
                except:
                    pass
        return data
    except Exception as e:
        print(f"[Warning] Failed to fetch reports from Supabase: {e}")
        raise e
