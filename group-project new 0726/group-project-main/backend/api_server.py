import os
import base64
import shutil
import time
from typing import TypedDict, Optional, List
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.vectorstores import Chroma
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from supabase_db import clear_ml_analysis_results, save_pr_report, supabase, SUPABASE_TABLE_NAME, SUPABASE_RESULT_TABLE_NAME, fetch_existing_result_ids, upsert_ml_analysis_result
from ml_analyzer import get_semantic_cache_telemetry, cache_monitor, MidEndAnalyzer
import logging as _logging
import joblib
import random
from pathlib import Path as _Path
from datetime import datetime, timezone
import csv
import json
import threading
import uuid
from urllib.parse import quote
from urllib.error import HTTPError
from urllib.request import Request as UrlRequest, urlopen

_log = _logging.getLogger(__name__)

# ─── ML Gatekeeper（第三段新增）────────────────────────────────────────────────
# 門檻從環境變數讀取，預設 0.7；不寫死，方便線上熱調整後重啟生效
ML_GATEKEEPER_THRESHOLD: float = float(os.environ.get("ML_GATEKEEPER_THRESHOLD", "0.7"))
_BASE_DIR = _Path(__file__).resolve().parents[1]
_MODELS_DIR = _BASE_DIR / "models"
_DASHBOARD_CSV_PATH = _BASE_DIR / "data" / "ml_dashboard_export.csv"
_PROMPTS_DIR = _BASE_DIR / "prompts"
_DASHBOARD_CACHE_TTL_SECONDS = int(os.environ.get("DASHBOARD_CACHE_TTL_SECONDS", "60"))
_dashboard_result_cache: dict[tuple, tuple[float, list[dict]]] = {}
_sync_job_lock = threading.Lock()
_sync_job: dict = {
    "id": None,
    "status": "idle",
    "phase": "idle",
    "processed": 0,
    "total": 0,
}


def _get_dashboard_cache(key: tuple) -> list[dict] | None:
    cached = _dashboard_result_cache.get(key)
    if not cached:
        return None
    created_at, rows = cached
    if time.time() - created_at > _DASHBOARD_CACHE_TTL_SECONDS:
        _dashboard_result_cache.pop(key, None)
        return None
    return rows


def _set_dashboard_cache(key: tuple, rows: list[dict]) -> None:
    _dashboard_result_cache[key] = (time.time(), rows)


def _clear_dashboard_cache() -> None:
    _dashboard_result_cache.clear()


def _load_prompt_file(filename: str, default: str = "") -> str:
    path = _PROMPTS_DIR / filename
    try:
        return path.read_text(encoding="utf-8").strip()
    except Exception as exc:
        _log.warning("[Prompts] failed to load %s: %s", filename, exc)
        return default


def _normalize_traditional_zh(text: str) -> str:
    """Keep dashboard AI output in Traditional Chinese without adding a dependency."""
    if not text:
        return ""
    replacements = {
        "核心痛点": "核心痛點",
        "行动建议": "行動建議",
        "回复草稿": "回覆草稿",
        "公开回复": "公開回覆",
        "顾客": "顧客",
        "顾": "顧",
        "这": "這",
        "个": "個",
        "为": "為",
        "与": "與",
        "专": "專",
        "业": "業",
        "务": "務",
        "态": "態",
        "体": "體",
        "验": "驗",
        "将": "將",
        "会": "會",
        "们": "們",
        "应": "應",
        "对": "對",
        "处": "處",
        "理": "理",
        "请": "請",
        "谢": "謝",
        "让": "讓",
        "给": "給",
        "过": "過",
        "还": "還",
        "长": "長",
        "间": "間",
        "题": "題",
        "议": "議",
        "议": "議",
        "议": "議",
        "内": "內",
        "关": "關",
        "键": "鍵",
        "风": "風",
        "险": "險",
        "级": "級",
        "标": "標",
        "签": "籤",
        "质": "質",
        "鲜": "鮮",
        "汤": "湯",
        "麦": "麥",
        "当": "當",
        "劳": "勞",
        "点": "點",
        "赞": "讚",
        "实": "實",
        "现": "現",
        "场": "場",
        "检": "檢",
        "查": "查",
        "员": "員",
        "补": "補",
        "偿": "償",
        "联系": "聯繫",
        "联": "聯",
        "认": "認",
        "证": "證",
        "单": "單",
        "产": "產",
        "门": "門",
        "满": "滿",
        "带": "帶",
        "净": "淨",
        "优": "優",
        "复": "覆",
    }
    normalized = text
    for source, target in replacements.items():
        normalized = normalized.replace(source, target)
    return normalized


def _load_ml_gatekeeper() -> tuple:
    """
    [新增] 主程式啟動時嘗試載入 ML 守門員（classifier.pkl / vectorizer.pkl）。
    若檔案不存在或載入失敗，log 錯誤並回傳 (None, None)，
    讓後續邏輯預設放行，不中斷服務。
    """
    clf_path = _MODELS_DIR / "classifier.pkl"
    vec_path = _MODELS_DIR / "vectorizer.pkl"
    try:
        clf = joblib.load(clf_path)
        vec = joblib.load(vec_path)
        _log.info("[ML Gatekeeper] ✅ 模型載入成功 | classifier: %s | vectorizer: %s",
                  clf_path, vec_path)
        return clf, vec
    except FileNotFoundError as exc:
        _log.warning(
            "[ML Gatekeeper] ⚠️ 模型檔案不存在（%s），預設放行所有請求。"
            "請先執行 build_ml_pipeline.py 訓練並匯出模型。", exc
        )
    except Exception as exc:
        _log.error(
            "[ML Gatekeeper] ❌ 模型載入失敗：%s，預設放行所有請求。", exc
        )
    return None, None


# 模組啟動時執行一次，避免每次請求重複 I/O
_ml_clf, _ml_vec = _load_ml_gatekeeper()


def _ml_predict_crisis_prob(text: str) -> float | None:
    """
    [新增] 以已載入的 ML 模型預測輸入文字為「實質危機客訴」（class=1）的機率。
    - 模型未就緒（None）→ 回傳 None，守門員透明旁路
    - 任何推論異常 → log 並回傳 None，不中斷主流程
    """
    if _ml_clf is None or _ml_vec is None:
        return None
    try:
        X = _ml_vec.transform([text])
        proba = _ml_clf.predict_proba(X)[0]
        classes = list(_ml_clf.classes_)
        return float(proba[classes.index(1)])
    except Exception as exc:
        _log.warning("[ML Gatekeeper] 推論失敗：%s，略過守門員直接放行。", exc)
        return None


def _heuristic_crisis_prob(text: str, rating: int | None = None) -> float:
    """Fallback used only when the trained pickle files are unavailable."""
    text = text or ""
    score = 0.15
    negative_words = [
        "難吃", "很爛", "糟", "生氣", "失望", "態度差", "不會再來",
        "噁心", "髒", "蟲", "蒼蠅", "拉肚子", "中毒", "投訴", "檢舉",
    ]
    positive_words = ["好吃", "推薦", "親切", "滿意", "新鮮", "會再來", "讚"]
    score += sum(0.1 for word in negative_words if word in text)
    score -= sum(0.08 for word in positive_words if word in text)
    if rating is not None:
        if rating <= 1:
            score += 0.25
        elif rating == 2:
            score += 0.15
        elif rating >= 4:
            score -= 0.15
    return min(max(score, 0.03), 0.98)


def _risk_level(score: int) -> str:
    if score >= 80:
        return "critical"
    if score >= 60:
        return "high"
    if score >= 35:
        return "medium"
    return "low"


def _topic_tag(text: str) -> str:
    text = text or ""
    if any(word in text for word in ["服務", "店員", "態度", "排隊", "等"]):
        return "service"
    if any(word in text for word in ["環境", "座位", "廁所", "髒", "衛生"]):
        return "environment"
    if any(word in text for word in ["貴", "價格", "划算", "價錢", "CP"]):
        return "price"
    return "food"


def _is_positive_context_review(text: str, rating: int | None = None) -> bool:
    text = text or ""
    positive_phrases = [
        "好吃", "好喝", "推薦", "讚", "滿意", "親切", "新鮮", "大推", "會再來",
        "超快", "很快", "速度快", "出餐快", "出餐速度超快", "有效率",
        "空間大", "空間蠻大", "空間很大", "店面空間蠻大", "店面空間很大",
        "不會等太久", "不用等太久", "不需等太久", "不必等太久",
        "不會等很久", "不用等很久", "沒有等很久", "不需排很久",
    ]
    hard_negative_phrases = [
        "不好吃", "很難吃", "難吃", "態度差", "很差", "失望", "髒", "蟲", "蒼蠅",
        "中毒", "拉肚子", "檢舉", "投訴", "提告", "不會再來", "等很久", "等太久", "太慢",
    ]
    negated_waiting = any(
        phrase in text
        for phrase in ["不會等太久", "不用等太久", "不需等太久", "不必等太久", "不會等很久", "不用等很久", "沒有等很久", "不需排很久"]
    )
    has_positive = any(phrase in text for phrase in positive_phrases)
    has_hard_negative = any(phrase in text for phrase in hard_negative_phrases) and not negated_waiting
    return (has_positive or negated_waiting or (rating is not None and rating >= 4 and not has_hard_negative)) and not has_hard_negative


def _rule_based_content_quality(text: str, record: dict) -> dict | None:
    text = (text or "").strip()
    platform = (record.get("platform") or "").lower()
    post_title = record.get("post_title") or ""
    short_noise = {
        "推", "幫推", "高調", "幫高調", "已站內", "圖呢", "圖呢？", "qq", "QQ", "+1",
        "讚", "好", "可", "哈", "哈哈", "呵", "路過", "卡", "蹲", "收", "私",
    }

    if not text:
        return {
            "is_meaningful": False,
            "content_type": "meaningless",
            "content_quality_score": 0,
            "filter_reason": "rule: empty_content",
        }
    if text in short_noise or len(text) <= 3:
        return {
            "is_meaningful": False,
            "content_type": "meaningless",
            "content_quality_score": 10,
            "filter_reason": "rule: too_short_or_reaction_only",
        }
    if any(word in text for word in ["站內", "私訊", "已私", "收信", "已售", "售出", "排隊收"]):
        return {
            "is_meaningful": False,
            "content_type": "non_customer_comment",
            "content_quality_score": 20,
            "filter_reason": "rule: transaction_or_private_message",
        }
    if len(text) <= 8 and not any(word in text for word in ["好吃", "難吃", "服務", "態度", "排隊", "價格", "環境", "衛生"]):
        return {
            "is_meaningful": False,
            "content_type": "meaningless",
            "content_quality_score": 15,
            "filter_reason": "rule: short_without_review_signal",
        }
    if platform == "ptt" and any(word in post_title for word in ["新聞", "閒聊", "問卦", "徵求", "商業"]):
        return {
            "is_meaningful": False,
            "content_type": "news_discussion",
            "content_quality_score": 35,
            "filter_reason": "rule: forum_discussion_context",
        }
    strong_review_signals = [
        "好吃", "難吃", "服務", "態度", "排隊", "等很久", "不用等", "出餐", "餐點",
        "價格", "太貴", "便宜", "環境", "衛生", "份量", "湯頭", "口味", "推薦",
        "再來", "不會再", "失望", "滿意", "店員", "內用", "外帶",
    ]
    if len(text) >= 20 and any(word in text for word in strong_review_signals):
        return {
            "is_meaningful": True,
            "content_type": "meaningful_review",
            "content_quality_score": 85,
            "filter_reason": "rule: substantive_review_signal",
        }
    return None


def _fallback_content_quality(text: str, record: dict, reason: str = "heuristic") -> dict:
    rule_result = _rule_based_content_quality(text, record)
    if rule_result is not None:
        return rule_result
    return {
        "is_meaningful": True,
        "content_type": "meaningful_review",
        "content_quality_score": 60,
        "filter_reason": f"{reason}: uncertain_default_meaningful",
    }


def _classify_content_quality_with_ollama(text: str, record: dict) -> dict:
    text = (text or "").strip()
    rule_result = _rule_based_content_quality(text, record)
    if rule_result is not None:
        return rule_result

    allowed_types = {
        "meaningful_review",
        "meaningless",
        "spam_or_noise",
        "non_customer_comment",
        "news_discussion",
    }
    prompt = f"""
你是餐飲輿情資料清洗分類器。請判斷下面這筆留言是否是「有實質消費體驗的評論」。

只能回傳 JSON，不要加任何解釋文字。

content_type 只能是以下五種之一：
- meaningful_review: 有實質評論，包含餐點、服務、價格、環境、等待、消費體驗、再訪意願等具體內容
- meaningless: 無意義或太短的留言，例如「推」「高調」「圖呢」「QQ」「已站內」
- spam_or_noise: 垃圾、灌水、亂碼、重複、廣告、無法判讀
- non_customer_comment: 非消費體驗，例如政治謾罵、閒聊、站內信、交易、單純討論人事物
- news_discussion: 針對新聞/文章/社群貼文事件的討論，不是在描述自己的消費體驗

JSON 格式：
{{
  "is_meaningful": true 或 false,
  "content_type": "meaningful_review|meaningless|spam_or_noise|non_customer_comment|news_discussion",
  "content_quality_score": 0 到 100 的整數,
  "filter_reason": "用繁體中文簡短說明原因"
}}

平台：{record.get("platform") or ""}
店家：{record.get("business_name") or ""}
文章標題：{record.get("post_title") or ""}
留言內容：
{text}
""".strip()

    try:
        llm = ChatOllama(
            model=os.environ.get("OLLAMA_MODEL", "qwen2.5:3b"),
            base_url=os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434"),
            temperature=0,
        )
        response = llm.invoke(prompt)
        raw = (response.content or "").strip()
        start = raw.find("{")
        end = raw.rfind("}")
        if start < 0 or end < start:
            raise ValueError(f"Ollama returned non-JSON content: {raw[:120]}")
        payload = json.loads(raw[start : end + 1])
        content_type = str(payload.get("content_type") or "").strip()
        if content_type not in allowed_types:
            raise ValueError(f"Invalid content_type: {content_type}")
        score = int(payload.get("content_quality_score", 0))
        score = min(max(score, 0), 100)
        is_meaningful = bool(payload.get("is_meaningful"))
        if content_type != "meaningful_review":
            is_meaningful = False
        return {
            "is_meaningful": is_meaningful,
            "content_type": content_type,
            "content_quality_score": score,
            "filter_reason": str(payload.get("filter_reason") or "").strip()[:500],
        }
    except Exception as exc:
        return _fallback_content_quality(text, record, reason=f"ollama_failed:{exc}")


def _dashboard_row_from_review(record: dict, index: int = 0, classify_content: bool = False) -> dict:
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

    ml_prob = _ml_predict_crisis_prob(text)
    prob = ml_prob if ml_prob is not None else _heuristic_crisis_prob(text, rating)
    risk_score = int(round(prob * 100))

    if _is_positive_context_review(text, rating):
        sentiment_label = "positive"
        prob = min(prob, 0.18)
        risk_score = int(round(prob * 100))
    elif risk_score >= 60 or (rating is not None and rating <= 2):
        sentiment_label = "negative"
    elif risk_score <= 20 and (rating is None or rating >= 4):
        sentiment_label = "positive"
    else:
        sentiment_label = "neutral"

    anger = min(max(prob + (0.1 if sentiment_label == "negative" else -0.1), 0.0), 1.0)
    joy = min(max(1.0 - prob if sentiment_label == "positive" else 0.12, 0.0), 1.0)
    disappointment = min(max(prob * 0.75, 0.0), 1.0)

    row = {
        "review_id": record.get("review_id") or record.get("master_review_id") or record.get("id") or index + 1,
        "master_review_id": record.get("master_review_id"),
        "reviewer": record.get("reviewer") or record.get("author") or record.get("comment_author_name") or record.get("post_author_name") or "ML 分析",
        "review_time": record.get("review_time") or record.get("comment_published_at") or record.get("post_published_at") or record.get("published_at") or record.get("created_at") or datetime.now(timezone.utc).isoformat(),
        "raw_text": text,
        "rating": rating,
        "platform": record.get("platform") or "ML Pipeline",
        "business_name": record.get("business_name") or record.get("store_name") or "",
        "post_title": record.get("post_title") or "",
        "report_content": record.get("report_content") or "",
        "sentiment_label": sentiment_label,
        "sentiment_score": round((1 - prob) if sentiment_label == "positive" else -prob, 4),
        "risk_score": risk_score,
        "risk_level": _risk_level(risk_score),
        "flag_food_safety": any(word in text for word in ["蟲", "蒼蠅", "中毒", "拉肚子", "食安"]),
        "flag_legal_risk": any(word in text for word in ["檢舉", "提告", "消保", "法院", "投訴"]),
        "flag_hygiene_risk": any(word in text for word in ["髒", "衛生", "蟲", "蒼蠅"]),
        "emotion_joy": round(joy, 4),
        "emotion_anger": round(anger, 4),
        "emotion_disappointment": round(disappointment, 4),
        "reviews_tag": _topic_tag(text),
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
        "ml_model_loaded": _ml_clf is not None and _ml_vec is not None,
    }
    if classify_content:
        row.update(_fallback_content_quality(text, record, reason="ml_rule"))
    return row


def _export_dashboard_csv(rows: list[dict], csv_path: _Path = _DASHBOARD_CSV_PATH) -> None:
    """Write the latest dashboard rows for inspection in Excel/VS Code."""
    try:
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        fieldnames: list[str] = []
        for row in rows:
            for key in row.keys():
                if key not in fieldnames:
                    fieldnames.append(key)

        with csv_path.open("w", encoding="utf-8-sig", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
    except Exception as exc:
        _log.warning("[Dashboard CSV] export failed: %s", exc)


def _save_gatekeeper_intercept(review: str, rating: int, crisis_prob: float, master_review_id: Optional[int] = None) -> None:
    """
    [新增] 攔截記錄寫回 Supabase（risk_level / sentiment_score 欄位）。
    採用動態欄位偵測，僅寫入資料表實際存在的欄位，
    避免因欄位不存在（如舊 schema）導致寫入失敗。
    任何例外僅 log，絕對不影響主流程。
    """
    try:
        if master_review_id is None:
            _log.info("[ML Gatekeeper] 無 master_review_id (Ad-hoc 測試)，略過寫入資料庫以符合外鍵限制。")
            return
            
        from supabase_db import supabase as _sb, SUPABASE_RESULT_TABLE_NAME as _tbl
        if not _sb:
            return
        data: dict = {
            "master_review_id": master_review_id,
            "comment_content": review,
            "risk_level": "Low",
            "sentiment_score": round(crisis_prob, 4),
            "filter_reason": "[ML Gatekeeper] 低風險，自動攔截，未觸發 RAG。",
        }
        # 動態欄位過濾：只寫入資料表真正擁有的欄位
        try:
            sample = _sb.table(_tbl).select(",".join(data.keys())).limit(1).execute()
            if sample.data:
                cols = set(sample.data[0].keys())
                data = {k: v for k, v in data.items() if k in cols}
        except Exception:
            pass  # schema 偵測失敗時沿用完整 data，讓後端自行報錯
        _sb.table(_tbl).insert(data).execute()
    except Exception as exc:
        _log.warning(
            "[ML Gatekeeper] 攔截記錄寫入 Supabase 失敗（不影響主流程）：%s", exc
        )
# ────────────────────────────────────────────────────────────────────────────────



# 初始化 FastAPI 應用程式
app = FastAPI(
    title="文章牛肉湯 AI 雙引擎公關與社群分析 API 伺服器",
    description="提供前後端同學對接的 REST API。支援 OpenAI 雲端模型與本地 Ollama 模型動態雙引擎切換。",
    version="1.1.0"
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

laws_mtime = os.path.getmtime("laws.txt") if os.path.exists("laws.txt") else 0
menu_mtime = os.path.getmtime("menu.txt") if os.path.exists("menu.txt") else 0

# 讀取 RAG 資料庫
def get_vector_db(engine, api_key, ollama_url, filename, mtime):
    if not os.path.exists(filename):
        return None
        
    import shutil
    engine_name = "openai" if engine == "openai" else "ollama"
    db_dir = f"./chroma_db_{filename.split('.')[0]}_{engine_name}"
    
    if engine == "openai":
        if not api_key:
            return None
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small", openai_api_key=api_key)
    else:
        embeddings = OllamaEmbeddings(model="nomic-embed-text", base_url=ollama_url)
    
    marker_file = os.path.join(db_dir, "mtime_marker.txt")
    saved_mtime = 0.0
    if os.path.exists(marker_file):
        try:
            with open(marker_file, "r") as mf:
                saved_mtime = float(mf.read().strip())
        except:
            pass
            
    rebuild = not os.path.exists(db_dir) or len(os.listdir(db_dir)) == 0 or abs(mtime - saved_mtime) > 0.01
    
    try:
        if rebuild:
            if os.path.exists(db_dir):
                shutil.rmtree(db_dir)
            os.makedirs(db_dir, exist_ok=True)
            
            with open(filename, "r", encoding="utf-8") as f:
                text_content = f.read()
                
            # 1. RAG 文件切片：針對結構化與條列式文件 (法規/菜單)，採用以行 (Line-based) 為基礎的切片方式，確保每一項內容語意完整
            chunks = [line.strip() for line in text_content.split("\n") if line.strip()]
            
            db = Chroma.from_texts(
                texts=chunks, 
                embedding=embeddings, 
                persist_directory=db_dir
            )
            
            with open(marker_file, "w") as mf:
                mf.write(str(mtime))
        else:
            db = Chroma(
                persist_directory=db_dir, 
                embedding_function=embeddings
            )
        return db
    except Exception as e:
        print(f"初始化 {filename} 資料庫失敗：{str(e)}")
        return None

# 輿情擴散風險估算公式
def predict_diffusion_risk(sentiment, rating, has_image, text):
    if sentiment == "正面":
        return 3.0
    base_risk = 30.0
    # 1. 食安與法務高危詞（單詞即 +25 分，極限警戒）
    food_safety_words = ["蒼蠅", "蟑螂", "老鼠", "食物中毒", "腹瀉", "衛生局", "蟲", "異物", "黑心", "不乾淨", "噁心"]
    matched_fs = [w for w in food_safety_words if w in text]
    base_risk += len(matched_fs) * 25.0
    
    # 2. 服務與公關痛點詞（單詞 +14 分）
    service_words = ["記者", "投訴", "倒閉", "難吃", "態度差", "態度很差", "態度惡劣", "崩潰", "失望", "爛", "生氣", "檢舉", "消保官", "退款", "不會再來", "絕對不會", "很髒", "超髒"]
    matched_sv = [w for w in service_words if w in text]
    base_risk += len(matched_sv) * 14.0

    if has_image:
        base_risk += 20.0
    if rating == 1:
        base_risk += 15.0
    elif rating == 2:
        base_risk += 10.0
    elif rating == 3:
        base_risk += 5.0
    return min(max(base_risk, 0.0), 99.9)

# ----------------- LangGraph 狀態與節點定義 -----------------

class AgentState(TypedDict):
    customer_review: str
    rating: int
    image_base64: Optional[str]
    sentiment: Optional[str]
    cheat_sheet: Optional[str]
    risk_percent: Optional[float]
    selected_tone_instruction: str
    api_key: str
    ollama_url: str
    engine: str
    result_text: Optional[str]
    scores: Optional[dict]
    review_feedback: Optional[str]
    revision_count: int
    review_passed: bool
    review_history: list
    workflow_logs: List[dict]
    mock_mode: bool
    few_shot_examples: Optional[str]
    query_embedding: Optional[list]

# Node 1: 分類部門
def sentiment_analyzer_node(state: AgentState):
    review = state["customer_review"]
    if _is_positive_context_review(review, state.get("rating")):
        return {"sentiment": "正面"}

    if state["mock_mode"]:
        positive_keywords = ["好吃", "推薦", "讚", "甜", "嫩", "大推", "服務好", "親切", "滿意", "好喝", "招牌"]
        is_positive = any(kw in review for kw in positive_keywords)
        sentiment = "正面" if is_positive else "負面"
        return {"sentiment": sentiment}
        
    engine = state["engine"]
    if engine == "openai":
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, openai_api_key=state["api_key"])
    else:
        llm = ChatOllama(model="qwen2.5:3b", base_url=state["ollama_url"])
        
    prompt_template = _load_prompt_file(
        "sentiment_analyzer.txt",
        "請判定以下顧客評論的客訴本質為正面（好評）還是負面（抱怨/客訴）？僅需輸出「正面」或「負面」二字，不要輸出其他字眼。\n\n評論：{customer_review}",
    )
    prompt = prompt_template.format(customer_review=review)
    response = llm.invoke(prompt)
    sentiment = "正面" if "正面" in response.content else "負面"
    return {"sentiment": sentiment}

# Node 2: 情報與檢索部門
def rag_retriever_node(state: AgentState):
    sentiment = state["sentiment"]
    customer_review = state["customer_review"]
    rating = state["rating"]
    api_key = state["api_key"]
    ollama_url = state["ollama_url"]
    engine = state["engine"]
    has_image = state["image_base64"] is not None
    
    filename = str(_BASE_DIR / "data" / ("laws.txt" if sentiment == "負面" else "menu.txt"))
    mtime = laws_mtime if sentiment == "負面" else menu_mtime
    few_shot_examples = ""
    query_embedding = None
    
    if state["mock_mode"]:
        cheat_sheet = ""
        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as f:
                cheat_sheet = "\n".join([line.strip() for line in f.readlines()[:2]])
        risk_percent = predict_diffusion_risk(sentiment, rating, has_image, customer_review)
        return {
            "cheat_sheet": cheat_sheet,
            "risk_percent": risk_percent
        }
        
    if engine == "ollama":
        # 本地 Ollama 模式：【關鍵提速優化】直接讀取整檔上下文，完全不呼叫向量模型
        cheat_sheet = ""
        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as f:
                cheat_sheet = f.read().strip()
    else:
        # 真實 OpenAI 模式：使用 ChromaDB 進行語意相似度檢索
        db_drawer = get_vector_db(engine, api_key, ollama_url, filename, mtime)
        cheat_sheet = ""
        if db_drawer:
            try:
                llm_rewriter = ChatOpenAI(model="gpt-4o-mini", temperature=0, openai_api_key=api_key)
                rewrite_prompt = f"請根據以下顧客評論，提煉出最核心的 2-3 個檢索關鍵字或法律/菜單主旨（如：法規名稱、特定菜色、衛生問題），只輸出關鍵字，以空格分隔。不要輸出任何其他文字。\n\n評論：{customer_review}"
                rewritten_query = llm_rewriter.invoke(rewrite_prompt).content.strip()
                
                # 建立 OpenAIEmbeddings 產生查詢向量與 Supabase 檢索
                try:
                    embeddings = OpenAIEmbeddings(model="text-embedding-3-small", openai_api_key=api_key)
                    query_embedding = embeddings.embed_query(rewritten_query)
                    from supabase_db import supabase, search_similar_reviews
                    if supabase:
                        similar_cases = search_similar_reviews(query_embedding, rating=rating, limit=2)
                        if similar_cases:
                            for i, case in enumerate(similar_cases):
                                few_shot_examples += f"【歷史案例 {i+1}】\n"
                                few_shot_examples += f"顧客評論：{case.get('review', '')}\n"
                                few_shot_examples += f"回覆報告：\n{case.get('report_content', '')}\n"
                                few_shot_examples += "----------------\n"
                except Exception as e_emb:
                    print(f"[Warning] Failed to generate embedding or query Supabase: {e_emb}")
                    
                docs = db_drawer.similarity_search(rewritten_query, k=2)
            except Exception:
                docs = db_drawer.similarity_search(customer_review, k=2)
            cheat_sheet = "\n".join([doc.page_content for doc in docs])
        
    if not few_shot_examples:
        few_shot_examples = "（尚無歷史相似範本，請依公關專業直接撰寫）\n"
        
    risk_percent = predict_diffusion_risk(sentiment, rating, has_image, customer_review)
    return {
        "cheat_sheet": cheat_sheet,
        "risk_percent": risk_percent,
        "few_shot_examples": few_shot_examples,
        "query_embedding": query_embedding
    }

# Node 3: 公關生成部門
def pr_generator_node(state: AgentState):
    sentiment = state["sentiment"]
    customer_review = state["customer_review"]
    api_key = state["api_key"]
    ollama_url = state["ollama_url"]
    engine = state["engine"]
    cheat_sheet = state["cheat_sheet"]
    selected_tone_instruction = state["selected_tone_instruction"]
    image_base64 = state["image_base64"]
    has_image = image_base64 is not None
    
    review_feedback = state.get("review_feedback", "")
    revision_count = state.get("revision_count", 0)
    
    if state["mock_mode"]:
        if sentiment == "負面":
            img_desc = "\n【🔍 顧客上傳照片視覺事證分析結果 (模擬)】：\n* 模擬檢驗結果：上傳照片的碗湯表面確實有一隻疑似蒼蠅的黑色小蟲。建議店家對此保留監視器並加強廚房消毒。"
            result_text = f"""{img_desc}

### 📊 1. 危機評估
* **危機等級**：🔴 高 / 黑色警戒（涉及食品安全，危機程度高）
* **核心關鍵字**：食品衛生、店員態度、餐點有蟲
* **影響評估**：涉及食安，若處理不慎極易引發網路爆料與商譽受損。

### ⚖️ 2. 法務與內部應對策略（限店家內部看）
* **適用法規**：食品安全衛生管理法第 8 條（業者應符合食品良好衛生規範準則，不潔導致損害需負責）。

### 📢 3. 公開回覆草稿（用於 Google 評論回覆）
> 敬愛的顧客您好，我是文章牛肉湯的負責人。非常抱歉讓您在我們店內喝到異物。我們已要求清潔公司加強廚房消毒，並對當班員工進行教育訓練。懇請您與我們聯絡，讓我們能為您全額退款並提供適當補償，非常抱歉。
"""
            scores = {"SINCERITY": 95, "LEGAL_DEFENSE": 90, "REPUTATION_RECOVERY": 92}
        else:
            result_text = """### 🌟 1. 滿意度分析
* **好評亮點**：溫體牛肉嫩、高湯鮮甜

### 📢 2. 公開致謝與推薦回覆
> 您好！非常感謝您對文章牛肉湯的支持與好評推薦！下次來店時，強烈推薦您也試試我們的「牛肉燥飯」和「五花牛肉湯」喔，絕對是老饕們極力推薦的黃金必點拍檔！期待很快再次見到您！
"""
            scores = {"SINCERITY": 98, "LEGAL_DEFENSE": 60, "REPUTATION_RECOVERY": 96}
        return {"result_text": result_text, "scores": scores}
        
    # 真實生成
    if engine == "openai":
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, openai_api_key=api_key)
    else:
        llm = ChatOllama(model="qwen2.5:3b", base_url=ollama_url, temperature=0.7)
        
    feedback_clause = ""
    if review_feedback and sentiment == "負面":
        feedback_clause = f"\n⚠️ 【退回修正警告】：\n您前一次撰寫的回覆被總監退回。退回意見如下：\n「{review_feedback}」\n這是第 {revision_count} 次修改，請重寫！\n"
        
    if engine == "ollama":
        if sentiment == "負面":
            system_template = f"""
            你現在是台南知名排隊名店【文章牛肉湯】的「資深公關危機總監」。請根據提供的【法律小抄】和【客訴評論】，撰寫一份精簡的公關回應報告。
            請勿產出多餘字眼，總長度控制在 150 字內，格式必須嚴格如下：
            
            ### 📊 1. 危機評估
            * 危機等級：🔴 高 (涉及食品安全)
            * 核心關鍵字：食品衛生
            
            ### 📢 2. 公開回覆草稿 (Google 評論回覆)
            > [請根據客訴評論的具體細節，誠懇且專業地撰寫回覆草稿，字數控制在 80-120 字內，開頭請帶入負責人稱呼，語氣誠懇有溫度，並請顧客私訊聯繫以便安排退款與補償。避免生硬地套用制式話術。]
            
            ---
            【法律小抄】：{{laws}}
            """
        else:
            system_template = f"""
            你現在是【文章牛肉湯】的「首席社群行銷經理」。請根據提供的【菜單小抄】和【好評評論】，寫一封精簡的回信。
            總長度控制在 150 字內，格式如下：
            
            ### 📢 1. 公開致謝與推薦回覆
            > [熱情感謝顧客，並根據菜單小抄精簡推薦 1 道招牌菜色，限制在 100 字內]
            
            ---
            【菜單小抄】：{{laws}}
            """
    else:
        if sentiment == "負面":
            system_template = """
            # 歷史優良回覆範例 (Few-shot Examples)
            {few_shot_examples}
            
            # 角色設定
            你現在是台南知名排隊名店【文章牛肉湯】的「資深公關危機暨法務策略總監」。請根據提供的【法律小抄】、【客訴評論】與【顧客佐證照片】（如有），為店家老闆產出一份極具策略性、條理清晰且可直接執行的「商家公關危機應對報告」。
            若有照片，請新增「【🔍 顧客上傳照片視覺事證分析結果】」說明是否有異物。
            回覆語氣：{tone_instruction}

            {feedback_clause}

            報告輸出格式（請以 Markdown 美化排版）：
            ### 📊 1. 危機評估
            * **危機等級**：[🔴 高 / 🟡 中 / 🟢 低]（請給出 1 句話的評估理由）
            ### ⚖️ 2. 法務與內部應對策略
            * **適用法規**：結合【法律小抄】說明法規。
            ### 📢 3. 公開回覆草稿（用於 Google 評論回覆）
            > **【回覆內文】**：（撰寫公開道歉信）
            ### ✉️ 4. 私訊安撫與補償模板

            # AI 自主評分要求
            [SCORE_START]
            SINCERITY: [分數]
            LEGAL_DEFENSE: [分數]
            REPUTATION_RECOVERY: [分數]
            [SCORE_END]
            ---
            【法律小抄】：{laws}
            """
        else:
            system_template = """
            # 歷史優良回覆範例 (Few-shot Examples)
            {few_shot_examples}
            
            # 角色設定
            你現在是台南知名排隊名店【文章牛肉湯】的「首席社群品牌與行銷經理」。請根據提供的【菜單小抄】與【好評評論】，寫一封熱情誠摯的致謝回覆並推薦 1-2 道招牌菜。
            回覆語氣：{tone_instruction}

            報告輸出格式：
            ### 🌟 1. 滿意度分析
            ### 📢 2. 公開致謝與推薦回覆
            ### 🎁 3. 常客專屬小驚喜建議

            # AI 自主評分要求
            [SCORE_START]
            SINCERITY: [分數]
            LEGAL_DEFENSE: [分數]
            REPUTATION_RECOVERY: [分數]
            [SCORE_END]
            ---
            【菜單小抄】：{laws}
            """
        
    few_shot_examples = state.get("few_shot_examples", "（尚無歷史相似範本，請依公關專業直接撰寫）\n")
    formatted_system = system_template.format(
        laws=cheat_sheet,
        tone_instruction=selected_tone_instruction,
        feedback_clause=feedback_clause if sentiment == "負面" else "",
        few_shot_examples=few_shot_examples
    )
    
    if has_image and engine == "openai":
        user_content = [
            {"type": "text", "text": f"顧客評論：\n{customer_review}"},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
        ]
        user_message = HumanMessage(content=user_content)
    elif has_image and engine == "ollama":
        user_message = HumanMessage(content=f"顧客評論：\n{customer_review}\n\n(系統視覺判定提示：顧客已上傳照片事證，照片中碗湯表面確實有一隻黑色昆蟲/蒼蠅)")
    else:
        user_message = HumanMessage(content=customer_review)
        
    messages = [SystemMessage(content=formatted_system), user_message]
    response = llm.invoke(messages)
    result_text = response.content
    
    score_start_idx = result_text.find("[SCORE_START]")
    score_end_idx = result_text.find("[SCORE_END]")
    scores = {"SINCERITY": 80, "LEGAL_DEFENSE": 80, "REPUTATION_RECOVERY": 80}
    report_content = result_text
    
    if score_start_idx != -1 and score_end_idx != -1:
        score_block = result_text[score_start_idx + len("[SCORE_START]"):score_end_idx].strip()
        report_content = (result_text[:score_start_idx] + result_text[score_end_idx + len("[SCORE_END]"):].strip())
        for line in score_block.split("\n"):
            if ":" in line:
                key, val = line.split(":", 1)
                key = key.strip().upper()
                try:
                    scores[key] = int(val.strip())
                except ValueError:
                    pass
                    
    return {
        "result_text": report_content,
        "scores": scores
    }

# Node 4: 審查部門 (品牌總監審查)
def pr_reviewer_node(state: AgentState):
    sentiment = state["sentiment"]
    result_text = state["result_text"]
    revision_count = state.get("revision_count", 0)
    engine = state["engine"]
    api_key = state["api_key"]
    ollama_url = state["ollama_url"]
    history = state.get("review_history", [])
    
    if state["mock_mode"]:
        return {"review_passed": True, "review_history": history}
        
    if sentiment == "正面" or revision_count >= 2 or engine == "ollama":
        return {"review_passed": True, "review_history": history}
        
    if engine == "openai":
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, openai_api_key=api_key)
    else:
        llm = ChatOllama(model="qwen2.5:3b", base_url=ollama_url)
        
    review_prompt = f"""
    你現在是【文章牛肉湯】的資深品牌監察總監。請評核以下由公關撰寫的公開道歉信，誠意評分必須大於或等於 88 分，且不能有任何推卸責任、與客人爭執之語氣。
    請嚴格以以下格式給出意見：
    【審查結果】：[通過 / 不通過]
    【退回修改意見】：[如果不通過，請給出修改要求；如果通過寫無]
    
    公關報告內容如下：
    {result_text}
    """
    response = llm.invoke(review_prompt)
    review_result = response.content
    passed = "通過" in review_result and "不通過" not in review_result.split("【審查結果】")[-1].split("\n")[0]
    
    feedback = ""
    if not passed:
        feedback = review_result.split("【退回修改意見】")[-1].strip() if "【退回修改意見】" in review_result else "公開道歉信語氣不夠誠誠懇，請重新修改。"
        history.append(f"❌ 第 {revision_count + 1} 次審查不通過。退回理由：{feedback}")
    else:
        history.append(f"✅ 第 {revision_count + 1} 次審查通過。")
        
    return {
        "review_passed": passed,
        "review_feedback": feedback,
        "revision_count": revision_count + 1,
        "review_history": history
    }

def route_after_review(state: AgentState):
    if state["review_passed"]:
        return END
    else:
        return "pr_generator"

# ----------------- LangGraph 工作流編譯 -----------------

def build_workflow():
    workflow = StateGraph(AgentState)
    workflow.add_node("sentiment_analyzer", sentiment_analyzer_node)
    workflow.add_node("rag_retriever", rag_retriever_node)
    workflow.add_node("pr_generator", pr_generator_node)
    workflow.add_node("pr_reviewer", pr_reviewer_node)
    
    workflow.add_edge(START, "sentiment_analyzer")
    workflow.add_edge("sentiment_analyzer", "rag_retriever")
    workflow.add_edge("rag_retriever", "pr_generator")
    workflow.add_edge("pr_generator", "pr_reviewer")
    
    workflow.add_conditional_edges(
        "pr_reviewer",
        route_after_review,
        {
            END: END,
            "pr_generator": "pr_generator"
        }
    )
    return workflow.compile()

app_workflow = build_workflow()

# ----------------- 全域實例化 AI 分析管線引擎 -----------------
# 實例化 MidEndAnalyzer 供非同步背景任務使用
# （註：若需傳入特定的 llm_client 或 embedding_client，可在此處調整）
analyzer = MidEndAnalyzer()

# ----------------- FastAPI Pydantic 模型定義 -----------------

class AnalyzeRequest(BaseModel):
    review: str
    rating: int = 1
    image_base64: Optional[str] = None
    tone: str = "標準"  # 標準, 溫柔熱情, 強硬自保
    engine: str = "openai"  # openai, ollama
    mock_mode: bool = False
    force_generate: bool = False
    persist: bool = True
    master_review_id: Optional[int] = None


class DashboardAnalyzeRequest(BaseModel):
    reviews: List[dict]


class DashboardReplyRequest(BaseModel):
    review: str
    rating: int = 1
    platform: str = ""
    risk_level: str = ""
    sentiment_label: str = ""
    tone: str = "標準"
    engine: str = "ollama"
    flag_food_safety: bool = False
    flag_legal_risk: bool = False
    flag_hygiene_risk: bool = False


class AiReplyProxyRequest(BaseModel):
    provider: str
    model: str
    api_key: str = ""
    endpoint: str = ""
    prompt: str
    temperature: float = 0.65

# ----------------- REST API 接口實作 -----------------

@app.post("/api/crawler/webhook", summary="接收爬蟲評論寫入完成的 Webhook", status_code=200)
def crawler_webhook_api(source_record: dict, background_tasks: BackgroundTasks):
    """
    爬蟲資料接收端點（非同步觸發 AI 分析）。
    此 API 會在接收到資料後立刻回傳 HTTP 200，保護爬蟲不會因為 LLM 分析過久而 Timeout。
    AI Pipeline 的分析任務會交由 FastAPI 的 BackgroundTasks 於背景安全執行。
    """
    # 觸發 AI 分析管線 (非阻塞呼叫)
    background_tasks.add_task(analyzer.analyze_review_pipeline, source_record)
    
    # 立刻回傳成功狀態，讓爬蟲端結案
    return {"status": "success", "message": "Crawler data received, AI pipeline started in background."}


@app.post("/api/analyze", summary="分析 Google 評論並生成公關與行銷報告")
def analyze_review_api(req: AnalyzeRequest):
    current_key = os.environ.get("OPENAI_API_KEY", "")
    
    # 決定引擎類型
    selected_engine = req.engine.lower()
    is_mock = req.mock_mode or (selected_engine == "openai" and (not current_key or current_key == "你的_sk-proj-開頭的Key"))
    
    tone_guidelines = {
        "標準": "請以誠懇、專業且冷靜的公關筆調撰寫。正面評論則展現溫暖謝意；負面評論則展現擔當，但字裡行間不過度承諾尚未確定的賠償細節，以防法律爭議。",
        "溫柔熱情": "如果是好評，請用超級熱情、充滿親和力的口吻感謝顧客；如果是差評，請用極度溫柔、柔軟且體貼的語氣撰寫，將顧客的感受放在第一位，最大化誠心致歉。",
        "強硬自保": "如果是好評，維持標準親切回覆；如果是差評，請在回覆中保持禮貌，但行文需點出「我們會調閱當日監視器與食材留樣做嚴格調查」。面對無端指控或威脅，以客氣卻堅定的措辭說明，強調惡意中傷將保留法律追訴權。"
    }
    
    selected_tone = tone_guidelines.get(req.tone, tone_guidelines["標準"])
    
    try:
        initial_state = {
            "customer_review": req.review,
            "rating": req.rating,
            "image_base64": req.image_base64,
            "sentiment": None,
            "cheat_sheet": None,
            "risk_percent": None,
            "selected_tone_instruction": selected_tone,
            "api_key": current_key if not is_mock else "MOCK_KEY",
            "ollama_url": "http://localhost:11434",
            "engine": "openai" if not is_mock and selected_engine == "openai" else ("ollama" if selected_engine == "ollama" else "離線模擬 (完全免費)"),
            "result_text": None,
            "scores": None,
            "review_feedback": None,
            "revision_count": 0,
            "review_passed": False,
            "review_history": [],
            "workflow_logs": [],
            "mock_mode": is_mock,
            "few_shot_examples": None,
            "query_embedding": None
        }
        
        # ── ML Gatekeeper 插入點（第三段新增）──────────────────────────────────
        # 嚴禁修改此區塊以下的 RAG / LLM 核心邏輯
        _crisis_prob = _ml_predict_crisis_prob(req.review)
        if _crisis_prob is not None:
            if _crisis_prob < ML_GATEKEEPER_THRESHOLD and not req.force_generate:
                _log.info(
                    "[ML Gatekeeper] 攔截 | prob=%.4f < threshold=%.2f | review=%.60s...",
                    _crisis_prob, ML_GATEKEEPER_THRESHOLD, req.review,
                )
                _save_gatekeeper_intercept(req.review, req.rating, _crisis_prob, req.master_review_id)
                return {
                    "sentiment": "無關",
                    "risk_percent": round(_crisis_prob * 100, 2),
                    "scores": {"SINCERITY": 0, "LEGAL_DEFENSE": 0, "REPUTATION_RECOVERY": 0},
                    "report_content": (
                        f"[ML Gatekeeper] 此輿情評估為低風險"
                        f"（危機機率 {_crisis_prob:.2%}），"
                        f"系統自動攔截，未觸發 RAG 流程。"
                    ),
                    "is_mock_run": False,
                    "engine_used": "ml_gatekeeper",
                    "review_history": [
                        f"[ML Gatekeeper] 危機機率 {_crisis_prob:.2%} "
                        f"< 門檻 {ML_GATEKEEPER_THRESHOLD:.2f}，攔截。"
                    ],
                }
            else:
                _log.info(
                    "[ML Gatekeeper] 放行 | prob=%.4f >= threshold=%.2f | review=%.60s...",
                    _crisis_prob, ML_GATEKEEPER_THRESHOLD, req.review,
                )
        # ────────────────────────────────────────────────────────────────────────
        
        final_state = app_workflow.invoke(initial_state)
        
        # 同步至 Supabase 資料庫
        if req.persist:
            save_pr_report(
                review=req.review,
                rating=req.rating,
                sentiment=final_state.get("sentiment"),
                risk_percent=final_state.get("risk_percent"),
                report_content=final_state.get("result_text"),
                engine=initial_state["engine"],
                embedding=final_state.get("query_embedding")
            )

        
        return {
            "sentiment": final_state["sentiment"],
            "risk_percent": final_state["risk_percent"],
            "scores": final_state["scores"],
            "report_content": final_state["result_text"],
            "is_mock_run": is_mock,
            "engine_used": final_state["engine"],
            "review_history": final_state.get("review_history", [])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI 工作流執行失敗：{str(e)}")


@app.get("/api/semantic-cache/stats", summary="查詢 RAG 語意快取 (Semantic Cache) 監控遙測指標與回應延遲")
def semantic_cache_stats_api():
    """獲取 ml_analyzer.py 中 RAG 語意快取的即時命中率 (Threshold = 0.95)、回應延遲與近期查詢記錄。"""
    try:
        return get_semantic_cache_telemetry()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"獲取語意快取統計失敗：{exc}")


@app.get("/api/ml-dashboard")
def ml_dashboard_data(limit: int = 500):
    try:
        from supabase_db import fetch_all_reports
        records = fetch_all_reports(limit=limit)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to fetch source reviews: {exc}")

    rows = [_dashboard_row_from_review(record, index) for index, record in enumerate(records)]
    _export_dashboard_csv(rows)
    return rows[:limit]


@app.get("/api/ml-dashboard-results")
def ml_dashboard_result_data(limit: int = 0, select: str = "", order: str = "comment_published_at.desc.nullslast", business_name: str = ""):
    try:
        from supabase_db import DASHBOARD_RESULT_SELECT, fetch_result_reports
        columns = select if select and select != "*" else DASHBOARD_RESULT_SELECT
        cache_key = ("ml-dashboard-results", int(limit or 0), columns, order, business_name)
        cached_rows = _get_dashboard_cache(cache_key)
        if cached_rows is not None:
            return cached_rows
        rows = fetch_result_reports(limit=limit, columns=columns, order=order, business_name=business_name)
        _set_dashboard_cache(cache_key, rows)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to fetch dashboard result rows: {exc}")

    return rows


@app.get("/api/supabase-query")
def supabase_query_compatible(table: str = "master_reviews_result", select: str = "*", limit: int = 0, order: str = "comment_published_at.desc.nullslast", business_name: str = ""):
    if table == SUPABASE_RESULT_TABLE_NAME or table == "master_reviews_result":
        return ml_dashboard_result_data(limit=limit, select=select, order=order, business_name=business_name)
    return ml_dashboard_data(limit=limit)


@app.get("/api/businesses")
def dashboard_business_options():
    try:
        from supabase_db import fetch_result_reports
        cache_key = ("business-options",)
        cached_rows = _get_dashboard_cache(cache_key)
        if cached_rows is not None:
            return cached_rows
        rows = fetch_result_reports(limit=0, columns="business_name", order="business_name.asc")
        counts: dict[str, int] = {}
        for row in rows:
            name = (row.get("business_name") or "未命名品牌").strip()
            counts[name] = counts.get(name, 0) + 1
        business_rows = [
            {"business_name": name, "count": count}
            for name, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
        ]
        _set_dashboard_cache(cache_key, business_rows)
        return business_rows
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to fetch business options: {exc}")



def _sync_job_snapshot() -> dict:
    with _sync_job_lock:
        return dict(_sync_job)


def _update_sync_job(job_id: str, **updates) -> None:
    with _sync_job_lock:
        if _sync_job.get("id") == job_id:
            _sync_job.update(updates)


def _execute_ml_dashboard_sync(
    job_id: str,
    limit: int | None = None,
    dry_run: bool = False,
    force: bool = False,
):
    _update_sync_job(job_id, phase="fetching_source")
    try:
        from supabase_db import fetch_all_reports
        records = fetch_all_reports()
    except Exception as exc:
        raise RuntimeError(f"Failed to fetch source reviews: {exc}") from exc

    existing_ids = set()
    if not force:
        _update_sync_job(job_id, phase="fetching_existing")
        try:
            existing_ids = fetch_existing_result_ids()
        except Exception as exc:
            raise RuntimeError(f"Failed to fetch existing result ids: {exc}") from exc

    _update_sync_job(job_id, phase="preparing")
    pending_records = []
    skipped_existing = 0
    for record in records:
        master_review_id = record.get("master_review_id") or record.get("review_id") or record.get("id")
        if not force and master_review_id in existing_ids:
            skipped_existing += 1
            continue
        pending_records.append(record)

    selected_records = pending_records if limit is None or limit <= 0 else pending_records[: max(1, min(limit, len(pending_records)))]
    rows = []
    _update_sync_job(job_id, phase="analyzing", processed=0, total=len(selected_records))
    for index, record in enumerate(selected_records):
        rows.append(_dashboard_row_from_review(record, index, classify_content=True))
        _update_sync_job(job_id, processed=index + 1)
    _export_dashboard_csv(rows)

    cleared_rows = 0
    if force and not dry_run:
        _update_sync_job(job_id, phase="clearing_results", processed=0, total=0)
        clear_result = clear_ml_analysis_results()
        if clear_result.get("status") != "success":
            raise RuntimeError(
                f"Failed to clear existing result rows: {clear_result.get('message', 'Unknown error')}"
            )
        cleared_rows = clear_result.get("deleted", 0)

    results = []
    _update_sync_job(job_id, phase="writing_results", processed=0, total=len(selected_records))
    for index, (record, row) in enumerate(zip(selected_records, rows)):
        results.append(upsert_ml_analysis_result(record, row, dry_run=dry_run))
        _update_sync_job(job_id, processed=index + 1)

    summary = {
        "dry_run": dry_run,
        "source_table": SUPABASE_TABLE_NAME,
        "result_table": SUPABASE_RESULT_TABLE_NAME,
        "requested_limit": limit,
        "force": force,
        "cleared_rows": cleared_rows,
        "source_total": len(records),
        "existing_result_rows": len(existing_ids),
        "skipped_existing": skipped_existing,
        "pending_total": len(pending_records),
        "total": len(results),
        "updated": sum(1 for result in results if result.get("status") == "success"),
        "would_update": sum(1 for result in results if result.get("status") == "dry_run"),
        "skipped": sum(1 for result in results if result.get("status") == "skipped"),
        "failed": sum(1 for result in results if result.get("status") == "error"),
        "results": results[:20],
    }
    if not dry_run and (summary["cleared_rows"] or summary["updated"] or summary["failed"]):
        _clear_dashboard_cache()
    return summary


def _run_ml_dashboard_sync_job(job_id: str, limit: int | None, dry_run: bool, force: bool) -> None:
    try:
        summary = _execute_ml_dashboard_sync(job_id, limit=limit, dry_run=dry_run, force=force)
    except Exception as exc:
        _log.exception("[Dashboard Sync] background job %s failed", job_id)
        _update_sync_job(
            job_id,
            status="failed",
            phase="failed",
            error=str(exc),
            finished_at=datetime.now(timezone.utc).isoformat(),
        )
        return

    _update_sync_job(
        job_id,
        status="completed",
        phase="completed",
        processed=summary.get("total", 0),
        total=summary.get("total", 0),
        summary=summary,
        finished_at=datetime.now(timezone.utc).isoformat(),
    )


@app.post("/api/ml-dashboard/sync", status_code=202)
def sync_ml_dashboard_to_supabase(
    limit: int | None = None,
    dry_run: bool = False,
    force: bool = False,
):
    """Start one non-blocking dashboard sync job."""
    if force and limit is not None and limit > 0:
        raise HTTPException(status_code=400, detail="Full rebuild does not support a row limit")

    with _sync_job_lock:
        if _sync_job.get("status") == "running":
            return {
                "accepted": False,
                "already_running": True,
                "job": dict(_sync_job),
            }

        job_id = uuid.uuid4().hex
        _sync_job.clear()
        _sync_job.update({
            "id": job_id,
            "status": "running",
            "phase": "queued",
            "processed": 0,
            "total": 0,
            "force": force,
            "dry_run": dry_run,
            "requested_limit": limit,
            "started_at": datetime.now(timezone.utc).isoformat(),
        })
        job_snapshot = dict(_sync_job)

    worker = threading.Thread(
        target=_run_ml_dashboard_sync_job,
        args=(job_id, limit, dry_run, force),
        daemon=True,
        name=f"dashboard-sync-{job_id[:8]}",
    )
    worker.start()
    return {"accepted": True, "already_running": False, "job": job_snapshot}


@app.get("/api/ml-dashboard/sync/status")
def ml_dashboard_sync_status(job_id: str | None = None):
    job = _sync_job_snapshot()
    if job_id and job.get("id") != job_id:
        raise HTTPException(status_code=404, detail="Sync job not found; the service may have restarted")
    return {"job": job}


@app.post("/api/ml-dashboard/analyze")
def analyze_dashboard_rows(req: DashboardAnalyzeRequest):
    rows = [_dashboard_row_from_review(record, index) for index, record in enumerate(req.reviews)]
    _export_dashboard_csv(rows)
    return rows


class ResolveReviewRequest(BaseModel):
    review_id: str
    response_text: str


@app.post("/api/reviews/resolve", summary="將產生的回覆內容寫入資料庫並結案")
def resolve_review_api(req: ResolveReviewRequest):
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase client not initialized")
    try:
        try:
            db_id = int(req.review_id)
        except ValueError:
            db_id = req.review_id
            
        update_data = {
            "reviews_response": req.response_text
        }
        
        # Write generated replies to the dashboard result table, not the source master_reviews table.
        try:
            sample = supabase.table(SUPABASE_RESULT_TABLE_NAME).select("status").limit(1).execute()
            if sample.data and len(sample.data) > 0:
                if "status" in sample.data[0]:
                    update_data["status"] = "resolved"
        except Exception:
            pass

        key_candidates = ("master_review_id", "review_id", "id")
        res = None
        for key in key_candidates:
            try:
                candidate = supabase.table(SUPABASE_RESULT_TABLE_NAME).update(update_data).eq(key, db_id).execute()
                if candidate.data:
                    res = candidate
                    break
            except Exception:
                continue
        if res is None:
            raise HTTPException(status_code=404, detail=f"找不到可更新的評論資料列：{SUPABASE_RESULT_TABLE_NAME}")
            
        if not res.data:
            raise HTTPException(status_code=404, detail=f"Review not found in {SUPABASE_RESULT_TABLE_NAME}")

        _clear_dashboard_cache()
        return {"status": "success", "table": SUPABASE_RESULT_TABLE_NAME, "data": res.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database update failed: {str(e)}")


@app.post("/api/dashboard-reply")
def generate_dashboard_reply(req: DashboardReplyRequest):
    """Generate a dashboard reply without writing anything back to Supabase."""
    review = (req.review or "").strip()
    if not review:
        raise HTTPException(status_code=400, detail="review is required")

    positive_words = [
        "好吃", "好喝", "推薦", "讚", "滿意", "親切", "新鮮", "嫩", "大推", "會再來",
        "超快", "很快", "速度快", "出餐快", "出餐速度超快", "像麥當勞", "有效率",
        "空間大", "空間蠻大", "空間很大", "店面空間蠻大", "店面空間很大",
        "不會等太久", "不用等太久", "不需等太久", "不必等太久", "不會等很久", "不用等很久"
    ]
    negative_words = [
        "不好", "很差", "差", "太慢", "慢", "等很久", "久等", "髒", "蟲", "蒼蠅",
        "中毒", "檢舉", "投訴", "態度差", "沒道歉", "失望", "不會再來"
    ]
    negated_waiting_praise = any(
        phrase in review
        for phrase in ["不會等太久", "不用等太久", "不需等太久", "不必等太久", "不會等很久", "不用等很久"]
    )
    has_positive = any(word in review for word in positive_words) or negated_waiting_praise
    has_negative = any(word in review for word in negative_words) and not negated_waiting_praise
    sentiment_label = (req.sentiment_label or "").lower()

    negative = (
        req.flag_food_safety
        or req.flag_legal_risk
        or req.flag_hygiene_risk
        or (has_negative and not has_positive)
        or (sentiment_label == "negative" and not has_positive)
        or (req.rating <= 2 and not has_positive)
        or ((req.risk_level or "").lower() in {"critical", "high"} and not has_positive)
    )

    knowledge_file = str(_BASE_DIR / "data" / ("laws.txt" if negative else "menu.txt"))
    knowledge = ""
    if os.path.exists(knowledge_file):
        with open(knowledge_file, "r", encoding="utf-8") as fh:
            knowledge = fh.read().strip()[:3000]

    risk_notes = []
    if req.flag_food_safety:
        risk_notes.append("食安風險")
    if req.flag_legal_risk:
        risk_notes.append("法務/消保風險")
    if req.flag_hygiene_risk:
        risk_notes.append("衛生風險")
    if not risk_notes:
        risk_notes.append("一般體驗回饋")

    prompt_filename = "dashboard_reply_ollama_negative.txt" if negative else "dashboard_reply_ollama_positive.txt"
    prompt_template = _load_prompt_file(
        prompt_filename,
        "你是台南餐飲店家的資深客服與公關回覆專員。請根據單一顧客評論產生公開平台回覆。"
    )
    tone_instruction = (
        "誠懇致歉：承接感受、語氣柔軟、有溫度；若是正評則轉為熱情感謝，不要道歉。"
        if req.tone == "誠懇致歉"
        else "專業說明：冷靜、具體、流程導向；少用情緒字眼，避免過度承諾。"
    )
    judgment = "正向稱讚" if has_positive and not negative else "負向/需安撫" if negative else "中性回饋"
    variation_instruction = random.choice([
        "句型請偏自然口語，開頭不要使用制式『您好，感謝您』。",
        "句型請偏穩重品牌語氣，避免與前次回覆使用相同開頭。",
        "請優先引用評論中的具體亮點或痛點作為回覆核心。",
        "請讓回覆更精簡，避免套版式收尾。",
    ])

    try:
        system_prompt = prompt_template.format(
            review=review,
            platform=req.platform or "未指定",
            rating=req.rating,
            risk_level=req.risk_level or "未指定",
            sentiment_label=req.sentiment_label or "未指定",
            risk_notes="、".join(risk_notes),
            judgment=judgment,
            tone_instruction=tone_instruction,
            laws=knowledge or "目前沒有額外知識檔，請依餐飲客服專業回覆。",
        )
        system_prompt += (
            f"\n\n本次生成變體要求：{variation_instruction}"
            "\n請在不偏離事實的前提下，避免產生與上一版幾乎相同的文字。"
            "\n無論如何都必須完整輸出三段標題：### 核心痛點、### 行動建議、### 回覆草稿。"
        )
    except Exception as exc:
        _log.warning("[Dashboard Reply] prompt format failed: %s", exc)
        system_prompt = f"""
你是台南餐飲店家的資深客服與公關回覆專員。請只針對本則評論回覆。
評論：{review}
語氣：{tone_instruction}
判斷：{judgment}
參考資料：{knowledge}
本次生成變體要求：{variation_instruction}
無論如何都必須完整輸出三段標題：### 核心痛點、### 行動建議、### 回覆草稿。
請輸出：### 核心痛點、### 行動建議、### 回覆草稿
"""

    if req.engine.lower() == "ollama":
        llm = ChatOllama(model="qwen2.5:3b", base_url="http://localhost:11434", temperature=0.7)
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"本則顧客評論：\n{review}")
        ])
        report_content = _normalize_traditional_zh(response.content)
        generation_mode = "ollama"
    else:
        if negative:
            opening = "您好，非常抱歉讓您有這次不舒服的體驗。" if req.tone == "誠懇致歉" else "您好，感謝您提供具體回饋。"
            action = "我們會檢視當日服務流程與現場狀況，並加強同仁訓練與內部查核。"
        else:
            opening = "您好，謝謝您溫暖的肯定！" if req.tone == "誠懇致歉" else "您好，感謝您分享這次用餐體驗。"
            action = "我們會把您的鼓勵轉達給現場夥伴，並持續維持出餐效率與餐點品質。"
        report_content = f"""### 核心痛點
{judgment}；評論重點：{review[:100]}
### 行動建議
{action}
### 回覆草稿
{opening}{action}期待未來還有機會為您服務，謝謝您的分享。"""
        report_content = _normalize_traditional_zh(report_content)
        generation_mode = "local_template"

    return {
        "report_content": report_content,
        "engine_used": req.engine.lower(),
        "generation_mode": generation_mode,
        "persisted": False,
        "prompt_used": prompt_filename,
        "judgment": judgment,
        "tone_used": req.tone,
    }


def _post_json(url: str, payload: dict, headers: dict, timeout: int = 60) -> dict:
    request = UrlRequest(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Provider HTTP {exc.code}: {body}") from exc


@app.post("/api/ai-reply")
def ai_reply_proxy(req: AiReplyProxyRequest):
    provider = (req.provider or "").lower().strip()
    model = (req.model or "").strip()
    env_key_names = {
        "gemini": "GEMINI_API_KEY",
        "huggingface": "HUGGINGFACE_API_KEY",
    }
    api_key = (req.api_key or "").strip() or os.environ.get(env_key_names.get(provider, ""), "").strip()
    prompt = (req.prompt or "").strip()
    temperature = float(req.temperature or 0.65)

    if provider not in {"gemini", "huggingface"}:
        raise HTTPException(status_code=400, detail="This proxy supports Gemini and Hugging Face only.")
    if not model:
        raise HTTPException(status_code=400, detail="Missing model.")
    if not api_key:
        raise HTTPException(status_code=400, detail=f"Missing API key. Set {env_key_names.get(provider)} in .env.")
    if not prompt:
        raise HTTPException(status_code=400, detail="Missing prompt.")

    try:
        if provider == "gemini":
            data = _post_json(
                f"https://generativelanguage.googleapis.com/v1beta/models/{quote(model, safe='')}:generateContent?key={quote(api_key, safe='')}",
                {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": temperature},
                },
                {"Content-Type": "application/json"},
            )
            parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
            reply = "".join(part.get("text", "") for part in parts).strip()
        else:
            data = _post_json(
                req.endpoint or "https://router.huggingface.co/v1/chat/completions",
                {
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": temperature,
                },
                {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                },
            )
            reply = (data.get("choices", [{}])[0].get("message", {}).get("content") or "").strip()

        if not reply:
            raise RuntimeError("Provider returned an empty response.")
        return {"reply": reply, "provider": provider, "model": model}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

@app.get("/")
def dashboard_home():
    return FileResponse(_BASE_DIR / "frontend" / "index.html")


@app.get("/dashboard")
def dashboard_page():
    return FileResponse(_BASE_DIR / "frontend" / "index.html")


@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "api_key_configured": bool(os.environ.get("OPENAI_API_KEY")),
        "ml_model_loaded": _ml_clf is not None and _ml_vec is not None,
    }

from fastapi.staticfiles import StaticFiles
app.mount("/", StaticFiles(directory=str(_BASE_DIR / "frontend")), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
