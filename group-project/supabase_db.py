import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Initialize Supabase client
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# 🎯【核心修改一】：最上面的環境變數預設值，直接改成阿嬤剛建好的實體大總表 master_reviews_enriched！
SUPABASE_TABLE_NAME = os.environ.get("SUPABASE_TABLE_NAME", "master_reviews_enriched")

if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"[Warning] Failed to initialize Supabase client: {e}")
        supabase = None
else:
    supabase = None
    print("[Info] SUPABASE_URL or SUPABASE_KEY not set. Supabase operations will be skipped.")


# 🎯【核心修改二】：將動態用戶端重置的預設資料表也同步改為新實體總表
def init_dynamic_client(url: str, key: str, table_name: str = "master_reviews_enriched"):
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
    【最終通關版：完美相容並對齊新實體總表欄位】
    """
    if not supabase:
        return {"status": "error", "message": "Supabase client not initialized"}
    
    try:
        # 準備資料字典，完全相容於新實體大總表的所有格子
        raw_data = {
            "raw_text": review,  # 完美對齊資料庫畫面上的 raw_text 欄位
            "rating": int(rating) if rating is not None else None,
            "sentiment": sentiment,
            "sentiment_label": sentiment,
            "risk_percent": float(risk_percent) if risk_percent is not None else None,
            "report_content": report_content,
            "engine": engine,
            "embedding": embedding
        }
        
        # 嘗試動態偵測資料表包含哪些欄位，防止多餘欄位導致失敗
        try:
            sample = supabase.table(SUPABASE_TABLE_NAME).select("*").limit(1).execute()
            if sample.data and len(sample.data) > 0:
                cols = set(sample.data[0].keys())
                data = {k: v for k, v in raw_data.items() if k in cols}
            else:
                # 🎯【核心修改三】：空表防護白名單（不含 embedding，master_reviews_enriched 無此欄）
                if SUPABASE_TABLE_NAME in ("review", "reviews_enriched", "master_reviews_enriched"):
                    cols = {"review_id", "reviewer", "review_time", "raw_text", "rating", "platform", "sentiment", "sentiment_label", "risk_percent", "report_content", "engine"}
                    data = {k: v for k, v in raw_data.items() if k in cols}
                else:
                    data = raw_data
        except Exception as e_schema:
            print(f"[Warning] Failed to fetch table schema, using default insert: {e_schema}")
            data = raw_data

        # 🔧 安全防護：移除值為 None 的欄位，避免 Supabase 拒絕不存在的 null 欄位
        data = {k: v for k, v in data.items() if v is not None}
            
        response = supabase.table(SUPABASE_TABLE_NAME).insert(data).execute()
        return {"status": "success", "data": response.data}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def search_similar_reviews(query_vector, rating, match_threshold=0.75, limit=3):
    """
    呼叫 Supabase SQL RPC (match_reviews) 進行向量相似度檢索，限制相同評分以保證情境一致。
    現階段優化：將 match_threshold 預設值調高至 0.75，並將 limit 擴大至 3。
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
            # 如果沒有 created_at 但有 review_id 或 id，則進行排序
            elif "review_id" in data[0]:
                try:
                    data = sorted(data, key=lambda x: x.get("review_id", 0), reverse=True)
                except:
                    pass
            elif "id" in data[0]:
                try:
                    data = sorted(data, key=lambda x: x.get("id", 0), reverse=True)
                except:
                    pass
        return data
    except Exception as e:
        print(f"[Warning] Failed to fetch reports from Supabase: {e}")
        raise e