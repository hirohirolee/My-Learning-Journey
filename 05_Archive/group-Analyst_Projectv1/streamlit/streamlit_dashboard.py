import json
import os
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv
from supabase import create_client


BASE_DIR = Path(__file__).resolve().parents[1]
HTML_PATH = BASE_DIR / "frontend" / "index.html"
DEFAULT_RESULT_TABLE = "master_reviews_result"
DEFAULT_COMPONENT_HEIGHT = 820


load_dotenv(BASE_DIR / ".env")


st.set_page_config(
    page_title="ML 輿情分析 Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
      [data-testid="stHeader"],
      [data-testid="stToolbar"],
      [data-testid="stSidebar"],
      [data-testid="stDecoration"],
      footer {
        display: none !important;
      }

      .block-container {
        padding: 0 !important;
        max-width: none !important;
      }

      .stApp,
      [data-testid="stAppViewContainer"],
      [data-testid="stMain"],
      [data-testid="stVerticalBlock"],
      [data-testid="stElementContainer"] {
        max-width: none !important;
        overflow-x: auto !important;
      }

      iframe {
        display: block;
        width: 100vw !important;
        max-width: none !important;
      }
    </style>
    """,
    unsafe_allow_html=True,
)


def get_config(name: str, default: str = "") -> str:
    """Read Streamlit secrets first, then local environment variables."""
    try:
        value = st.secrets.get(name)
        if value:
            return str(value)
    except Exception:
        pass
    try:
        lower_name = name.lower()
        if "supabase" in st.secrets and lower_name.startswith("supabase_"):
            nested_key = lower_name.replace("supabase_", "")
            value = st.secrets["supabase"].get(nested_key)
            if value:
                return str(value)
        if "openai" in st.secrets and lower_name == "openai_api_key":
            value = st.secrets["openai"].get("api_key")
            if value:
                return str(value)
    except Exception:
        pass
    return os.environ.get(name, default)


@st.cache_resource(show_spinner=False)
def get_supabase_client(url: str, key: str):
    if not url or not key:
        return None
    return create_client(url, key)


@st.cache_data(ttl=60, show_spinner="讀取 Supabase 資料中...")
def fetch_reports(url: str, key: str, table_name: str, limit: int) -> list[dict]:
    client = get_supabase_client(url, key)
    if client is None:
        return []

    def execute_select(start: int | None = None, end: int | None = None):
        query = client.table(table_name).select("*")
        if start is not None and end is not None:
            query = query.range(start, end)
        elif limit and limit > 0:
            query = query.limit(limit)
        return query.execute()

    if limit and limit > 0:
        response = execute_select()
        return response.data or []

    rows: list[dict] = []
    batch_size = 1000
    start = 0
    while True:
        end = start + batch_size - 1
        response = execute_select(start, end)
        batch = response.data or []
        rows.extend(batch)
        if len(batch) < batch_size:
            break
        start += batch_size
    return rows


def normalize_risk_level(score, existing_level: str | None = None) -> str:
    if existing_level:
        return existing_level
    try:
        numeric_score = float(score)
    except (TypeError, ValueError):
        return "low"
    if numeric_score >= 80:
        return "critical"
    if numeric_score >= 60:
        return "high"
    if numeric_score >= 35:
        return "medium"
    return "low"


def as_float(value, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def dashboard_row(record: dict, index: int) -> dict:
    text = (
        record.get("raw_text")
        or record.get("review")
        or record.get("content")
        or record.get("comment_content")
        or record.get("report_content")
        or ""
    )
    rating = record.get("rating")
    try:
        rating = int(rating) if rating is not None else None
    except (TypeError, ValueError):
        rating = None

    review_time = (
        record.get("review_time")
        or record.get("comment_published_at")
        or record.get("post_published_at")
        or record.get("published_at")
        or record.get("analyzed_at")
        or record.get("created_at")
    )
    risk_score = as_float(record.get("risk_score"), 0.0)
    sentiment_label = record.get("sentiment_label") or "neutral"
    reviews_response = record.get("reviews_response") or ""
    business_name = (
        record.get("businessName")
        or record.get("business_name")
        or record.get("busninessNAME")
        or record.get("store_name")
        or ""
    )

    return {
        **record,
        "review_id": record.get("review_id") or record.get("master_review_id") or record.get("id") or index + 1,
        "master_review_id": record.get("master_review_id") or record.get("review_id") or record.get("id") or index + 1,
        "reviewer": record.get("reviewer") or record.get("author") or record.get("comment_author_name") or record.get("post_author_name") or "ML 分析",
        "review_time": review_time,
        "raw_text": text,
        "comment_content": record.get("comment_content") or text,
        "rating": rating,
        "platform": record.get("platform") or "ML Pipeline",
        "businessName": business_name,
        "business_name": business_name,
        "post_title": record.get("post_title") or "",
        "report_content": record.get("report_content") or "",
        "sentiment_label": sentiment_label,
        "sentiment_score": as_float(record.get("sentiment_score"), 0.0),
        "risk_score": risk_score,
        "risk_level": normalize_risk_level(risk_score, record.get("risk_level")),
        "flag_food_safety": any(word in text for word in ["蟲", "蒼蠅", "中毒", "拉肚子", "食安"]),
        "flag_legal_risk": any(word in text for word in ["檢舉", "提告", "消保", "法院", "投訴"]),
        "flag_hygiene_risk": any(word in text for word in ["髒", "衛生", "蟲", "蒼蠅"]),
        "emotion_joy": as_float(record.get("emotion_joy"), 0.0),
        "emotion_anger": as_float(record.get("emotion_anger"), 0.0),
        "emotion_disappointment": as_float(record.get("emotion_disappointment"), 0.0),
        "reviews_tag": record.get("reviews_tag") or "",
        "analyzed_at": record.get("analyzed_at"),
        "is_meaningful": record.get("is_meaningful"),
        "content_type": record.get("content_type") or "unknown",
        "content_quality_score": as_float(record.get("content_quality_score"), 0.0),
        "filter_reason": record.get("filter_reason") or "",
        "reviews_response": reviews_response,
        "status": record.get("status") or ("resolved" if reviews_response else "pending"),
        "ml_model_loaded": False,
    }


def inject_dashboard_data(html: str, rows: list[dict], supabase_url: str, supabase_public_key: str, table_name: str) -> str:
    data_json = (
        json.dumps(rows, ensure_ascii=False)
        .replace("</", "<\\/")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )
    streamlit_config_json = (
        json.dumps(
            {
                "supabaseUrl": supabase_url,
                "supabaseKey": supabase_public_key,
                "tableName": table_name,
            },
            ensure_ascii=False,
        )
        .replace("</", "<\\/")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )
    streamlit_style = """
    <style id="streamlit-scroll-overrides">
      @media (max-width: 767px) {
        html,
        body.streamlit-embedded {
          height: auto !important;
          min-height: 100dvh !important;
          overflow-x: hidden !important;
          overflow-y: auto !important;
        }

        body.streamlit-embedded .app-shell,
        body.streamlit-embedded .app-main,
        body.streamlit-embedded #view-workspace,
        body.streamlit-embedded #view-trends,
        body.streamlit-embedded .workspace-shell,
        body.streamlit-embedded .overview-pane {
          height: auto !important;
          max-height: none !important;
          overflow: visible !important;
        }

        body.streamlit-embedded .app-main {
          min-height: 0 !important;
        }

        body.streamlit-embedded .overview-pane,
        body.streamlit-embedded #view-trends,
        body.streamlit-embedded #trend-event-list,
        body.streamlit-embedded .overview-pane .overflow-y-auto {
          overflow-y: visible !important;
          max-height: none !important;
        }
      }
    </style>
    """
    injected = html.replace(
        "window.PRE_INJECTED_DATA = null;",
        f"window.PRE_INJECTED_DATA = {data_json};\n        window.STREAMLIT_SUPABASE_CONFIG = {streamlit_config_json};",
    )
    injected = injected.replace("</head>", f"{streamlit_style}\n</head>")
    injected = injected.replace('<body class="', '<body class="streamlit-embedded ')
    injected = injected.replace(
        "autoRefreshTimer = setTimeout(loadData, 60000);",
        "autoRefreshTimer = null;",
    )
    return injected


supabase_url = get_config("SUPABASE_URL")
supabase_key = get_config("SUPABASE_KEY")
supabase_public_key = get_config("SUPABASE_PUBLIC_KEY") or get_config("SUPABASE_ANON_KEY")
table_name = get_config("SUPABASE_TABLE_NAME", DEFAULT_RESULT_TABLE)
limit = int(get_config("DASHBOARD_LIMIT", "0") or "0")
component_height = int(get_config("STREAMLIT_COMPONENT_HEIGHT", str(DEFAULT_COMPONENT_HEIGHT)) or DEFAULT_COMPONENT_HEIGHT)

if not supabase_url or not supabase_key:
    st.error("缺少 Supabase 設定。Streamlit Cloud 請到 Secrets 設定 SUPABASE_URL / SUPABASE_KEY / SUPABASE_TABLE_NAME。")
    st.code(
        """
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_KEY = "your-supabase-key"
SUPABASE_TABLE_NAME = "master_reviews_result"
        """.strip(),
        language="toml",
    )
    st.stop()

try:
    source_records = fetch_reports(supabase_url, supabase_key, table_name, limit)
except Exception as exc:
    st.error(f"讀取 Supabase 失敗：{exc}")
    st.caption(f"目前資料表設定：{table_name}")
    st.stop()

rows = [dashboard_row(record, index) for index, record in enumerate(source_records)]

if not rows:
    st.error("Supabase 已連線，但沒有讀到資料。請確認資料表名稱與 RLS 權限。")
    st.caption(f"目前資料表設定：{table_name}")
    st.stop()

if not HTML_PATH.exists():
    st.error(f"找不到 HTML 介面檔：{HTML_PATH}")
    st.stop()

dashboard_html = HTML_PATH.read_text(encoding="utf-8")
components.html(
    inject_dashboard_data(dashboard_html, rows, supabase_url, supabase_public_key, table_name),
    height=component_height,
    scrolling=True,
)
