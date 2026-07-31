import json
import os
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs, quote, urlparse
from urllib.request import Request, urlopen

import joblib


BASE_DIR = Path(__file__).resolve().parents[1]
MODELS_DIR = BASE_DIR / "models"

_MODEL_CACHE = {"classifier": None, "vectorizer": None, "loaded": False}


NEGATIVE_WORDS = [
    "\u96e3\u5403",
    "\u5f88\u721b",
    "\u7cdf",
    "\u751f\u6c23",
    "\u5931\u671b",
    "\u614b\u5ea6\u5dee",
    "\u614b\u5ea6\u5f88\u5dee",
    "\u4e0d\u6703\u518d",
    "\u5666\u5fc3",
    "\u9ad2",
    "\u87f2",
    "\u84bc\u8805",
    "\u62c9\u809a\u5b50",
    "\u4e2d\u6bd2",
    "\u6295\u8a34",
    "\u6aa2\u8209",
    "\u5d29\u6f70",
]

POSITIVE_WORDS = [
    "\u597d\u5403",
    "\u63a8\u85a6",
    "\u89aa\u5207",
    "\u6eff\u610f",
    "\u65b0\u9bae",
    "\u6703\u518d\u4f86",
    "\u8b9a",
    "\u4e0d\u932f",
]


def _json_response(handler: BaseHTTPRequestHandler, status: int, payload):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Cache-Control", "no-store")
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.end_headers()
    handler.wfile.write(body)


def _load_models():
    if _MODEL_CACHE["loaded"]:
        return _MODEL_CACHE["classifier"], _MODEL_CACHE["vectorizer"]

    try:
        _MODEL_CACHE["classifier"] = joblib.load(MODELS_DIR / "classifier.pkl")
        _MODEL_CACHE["vectorizer"] = joblib.load(MODELS_DIR / "vectorizer.pkl")
    except Exception:
        _MODEL_CACHE["classifier"] = None
        _MODEL_CACHE["vectorizer"] = None
    finally:
        _MODEL_CACHE["loaded"] = True

    return _MODEL_CACHE["classifier"], _MODEL_CACHE["vectorizer"]


def _fetch_supabase_rows(table_name: str, limit: int):
    supabase_url = os.environ.get("SUPABASE_URL", "").rstrip("/")
    supabase_key = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY", "")
    if not supabase_url or not supabase_key:
        raise RuntimeError("Missing SUPABASE_URL or SUPABASE_KEY")

    query = f"select=*&limit={limit}&order=review_time.desc.nullslast"
    url = f"{supabase_url}/rest/v1/{quote(table_name)}?{query}"
    request = Request(
        url,
        headers={
            "apikey": supabase_key,
            "Authorization": f"Bearer {supabase_key}",
            "Content-Type": "application/json",
        },
    )
    with urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def _ml_predict_crisis_prob(text: str, classifier, vectorizer) -> float | None:
    if classifier is None or vectorizer is None:
        return None
    try:
        x = vectorizer.transform([text])
        proba = classifier.predict_proba(x)[0]
        classes = list(classifier.classes_)
        return float(proba[classes.index(1)])
    except Exception:
        return None


def _heuristic_crisis_prob(text: str, rating: int | None = None) -> float:
    text = text or ""
    score = 0.15
    score += sum(0.1 for word in NEGATIVE_WORDS if word in text)
    score -= sum(0.08 for word in POSITIVE_WORDS if word in text)
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
    if any(word in text for word in ["\u670d\u52d9", "\u5e97\u54e1", "\u614b\u5ea6", "\u6392\u968a", "\u7b49"]):
        return "service"
    if any(word in text for word in ["\u74b0\u5883", "\u5ea7\u4f4d", "\u5ec1\u6240", "\u9ad2", "\u885b\u751f"]):
        return "environment"
    if any(word in text for word in ["\u8cb4", "\u50f9\u683c", "\u5212\u7b97", "\u50f9\u9322", "CP"]):
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


def _dashboard_row(record: dict, index: int, classifier, vectorizer) -> dict:
    text = (
        record.get("raw_text")
        or record.get("review")
        or record.get("content")
        or record.get("report_content")
        or ""
    )
    rating = record.get("rating")
    try:
        rating = int(rating) if rating is not None else None
    except (TypeError, ValueError):
        rating = None

    ml_prob = _ml_predict_crisis_prob(text, classifier, vectorizer)
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

    return {
        "review_id": record.get("review_id") or record.get("id") or index + 1,
        "reviewer": record.get("reviewer") or record.get("author") or "ML analysis",
        "review_time": record.get("review_time")
        or record.get("published_at")
        or record.get("created_at")
        or datetime.now(timezone.utc).isoformat(),
        "raw_text": text,
        "rating": rating,
        "platform": record.get("platform") or "ML Pipeline",
        "report_content": record.get("report_content") or "",
        "sentiment_label": sentiment_label,
        "sentiment_score": round((1 - prob) if sentiment_label == "positive" else -prob, 4),
        "risk_score": risk_score,
        "risk_level": _risk_level(risk_score),
        "flag_food_safety": any(word in text for word in ["\u87f2", "\u84bc\u8805", "\u4e2d\u6bd2", "\u62c9\u809a\u5b50", "\u98df\u5b89"]),
        "flag_legal_risk": any(word in text for word in ["\u6aa2\u8209", "\u63d0\u544a", "\u6d88\u4fdd", "\u6cd5\u9662", "\u6295\u8a34"]),
        "flag_hygiene_risk": any(word in text for word in ["\u9ad2", "\u885b\u751f", "\u87f2", "\u84bc\u8805"]),
        "emotion_joy": round(joy, 4),
        "emotion_anger": round(anger, 4),
        "emotion_disappointment": round(disappointment, 4),
        "reviews_tag": _topic_tag(text),
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
        "ml_model_loaded": classifier is not None and vectorizer is not None,
    }


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        try:
            query = parse_qs(urlparse(self.path).query)
            table_name = (
                query.get("table", [None])[0]
                or os.environ.get("SUPABASE_TABLE_NAME")
                or "master_reviews_enriched"
            )
            try:
                limit = int(query.get("limit", ["500"])[0])
            except ValueError:
                limit = 500
            limit = min(max(limit, 1), 5000)

            records = _fetch_supabase_rows(table_name, limit)
            classifier, vectorizer = _load_models()
            rows = [
                _dashboard_row(record, index, classifier, vectorizer)
                for index, record in enumerate(records)
            ]
            _json_response(self, 200, rows)
        except Exception as exc:
            _json_response(self, 500, {"error": str(exc)})
