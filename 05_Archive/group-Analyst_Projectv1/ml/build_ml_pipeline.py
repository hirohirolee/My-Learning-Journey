"""
build_ml_pipeline.py
─────────────────────────────────────────────────────────────────────────────
ML 守門員訓練管線（第二段 - 中端全功能完全收攏版）

流程：
  1. 從 Supabase 撈取歷史輿情
  2. 優先使用資料表既有標籤，不足時調用 LLM 補齊差額
  3. 特徵工程優化：Jieba 精準斷詞 + 停用詞清洗
  4. 機器學習訓練：RandomForestClassifier 處理樣本不平衡
  5. 匯出模型與特徵對照表至 ./models/
─────────────────────────────────────────────────────────────────────────────
"""

import os
import sys
import time
import logging
import math
import re
from pathlib import Path

# ── 0. 基本設定 ────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR / "backend"))

from dotenv import load_dotenv
load_dotenv(BASE_DIR / ".env")

ENGINE          = os.environ.get("ENGINE", "openai").lower()
OPENAI_API_KEY  = os.environ.get("OPENAI_API_KEY", "")
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL    = os.environ.get("OLLAMA_MODEL", "qwen2.5:3b")
MAX_RECORDS_ENV = os.environ.get("MAX_RECORDS", "")
BATCH_SIZE      = int(os.environ.get("BATCH_SIZE", "10"))
SLEEP_SECONDS   = float(os.environ.get("SLEEP_SECONDS", "1.0"))
MODELS_DIR      = BASE_DIR / "models"

MAX_RECORDS: int | None = int(MAX_RECORDS_ENV) if MAX_RECORDS_ENV.strip().isdigit() else None
MIN_TRAIN_SAMPLES = 150 

# ── 1. 撈取歷史資料 ────────────────────────────────────────────────────────

def fetch_reviews(max_records: int | None = None) -> list[dict]:
    log.info("📡 連接 Supabase，撈取歷史評論資料...")
    from supabase_db import fetch_all_reports
    try:
        records = fetch_all_reports()
    except Exception as exc:
        log.error("❌ fetch_all_reports() 失敗：%s", exc)
        raise SystemExit(1)

    normalized_records: list[dict] = []
    for record in records:
        text = (
            record.get("review")
            or record.get("raw_text")
            or record.get("content")
            or record.get("comment_content")
            or ""
        )
        if not str(text).strip():
            continue
        normalized = dict(record)
        normalized["review"] = str(text).strip()
        normalized_records.append(normalized)
    
    if max_records is not None:
        normalized_records = normalized_records[:max_records]
    return normalized_records


# ── 2. LLM 初始化 ──────────────────────────────────────────────────────────

def build_llm():
    if ENGINE == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(model=OLLAMA_MODEL, base_url=OLLAMA_BASE_URL, temperature=0)
    else:
        if not OPENAI_API_KEY:
            log.error("❌ ENGINE=openai 但 OPENAI_API_KEY 未設定。")
            raise SystemExit(1)
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model="gpt-4o-mini", temperature=0, openai_api_key=OPENAI_API_KEY)


# ── 3. LLM 自動打標籤 ──────────────────────────────────────────────────────

def label_with_llm(reviews: list[str], llm) -> tuple[list[str], list[int]]:
    from prompts.ml_prompts import PROMPT_STAGE_1

    kept_texts: list[str] = []
    kept_labels: list[int] = []
    discard_count = 0
    total = len(reviews)
    batches = math.ceil(total / BATCH_SIZE)

    for batch_idx in range(batches):
        start = batch_idx * BATCH_SIZE
        end   = min(start + BATCH_SIZE, total)
        batch = reviews[start:end]

        for i, text in enumerate(batch, start=start + 1):
            prompt = PROMPT_STAGE_1.format(text=text)
            try:
                response = llm.invoke(prompt)
                raw = response.content.strip()
            except Exception as exc:
                discard_count += 1
                continue

            match = re.search(r'\b([01])\b', raw)
            if not match:
                match = re.search(r'([01])', raw)

            if match:
                kept_texts.append(text)
                kept_labels.append(int(match.group(1)))
            else:
                discard_count += 1

        if batch_idx < batches - 1:
            time.sleep(SLEEP_SECONDS)

    return kept_texts, kept_labels


def is_positive_context_review(text: str, rating: int | None = None) -> bool:
    positive_phrases = ["好吃", "好喝", "推薦", "讚", "滿意", "親切", "不會等太久", "不用等太久"]
    hard_negative_phrases = ["不好吃", "很難吃", "態度差", "很差", "失望", "髒", "蟲", "蒼蠅", "拉肚子"]
    has_positive = any(phrase in text for phrase in positive_phrases)
    has_hard_negative = any(phrase in text for phrase in hard_negative_phrases)
    return has_positive and not has_hard_negative


def label_from_existing_fields(records: list[dict]) -> tuple[list[str], list[int]]:
    texts: list[str] = []
    labels: list[int] = []

    for record in records:
        text = record.get("review", "").strip()
        if not text:
            continue

        rating = record.get("rating")
        try: rating_num = int(rating) if rating is not None else None
        except (TypeError, ValueError): rating_num = None

        if is_positive_context_review(text, rating_num):
            texts.append(text)
            labels.append(0)
            continue

        label = None
        risk = record.get("risk_percent")
        if risk is not None:
            try: label = 1 if float(risk) >= 50 else 0
            except (TypeError, ValueError): pass

        if label is None:
            sentiment = str(record.get("sentiment") or record.get("sentiment_label") or "").lower()
            if sentiment == "negative": label = 1
            elif sentiment in {"positive", "neutral"}: label = 0

        if label is not None:
            texts.append(text)
            labels.append(label)

    return texts, labels


# ── 4. 訓練 ML 模型（Jieba 斷詞精準優化版） ──────────────────────────────────

def train_model(texts: list[str], labels: list[int]):
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, precision_score, recall_score, classification_report
    import jieba

    STOP_WORDS = {"的", "了", "在", "是", "我", "你", "他", "它", "們", "之", "於", "與", "及"}

    def chinese_tokenizer(text):
        return [word for word in jieba.cut(text) if word.strip() and word not in STOP_WORDS]

    log.info("⚙️  特徵工程：優化為 Jieba 斷詞與停用詞機制")
    vectorizer = TfidfVectorizer(
        tokenizer=chinese_tokenizer,
        analyzer="word",
        ngram_range=(1, 2),
        max_features=15_000,
        sublinear_tf=True,
        min_df=2
    )

    X = vectorizer.fit_transform(texts)
    y = labels

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    log.info("🌲 訓練 RandomForestClassifier 算盤中...")
    clf = RandomForestClassifier(n_estimators=200, class_weight="balanced", random_state=42, n_jobs=-1)
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    print(classification_report(y_test, y_pred, target_names=["無關(0)", "危機(1)"]))

    return vectorizer, clf


def main():
    log.info("🚀 ML 中端優化管線啟動")
    records = fetch_reviews(MAX_RECORDS)
    raw_texts = [r["review"] for r in records]

    texts, labels = label_from_existing_fields(records)

    if len(texts) < MIN_TRAIN_SAMPLES:
        needed = MIN_TRAIN_SAMPLES - len(texts)
        existing_set = set(texts)
        unlabeled_reviews = [text for text in raw_texts if text not in existing_set]
        
        if unlabeled_reviews:
            llm = build_llm()
            llm_texts, llm_labels = label_with_llm(unlabeled_reviews[:needed], llm)
            texts.extend(llm_texts)
            labels.extend(llm_labels)

    import joblib
    vectorizer, classifier = train_model(texts, labels)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(vectorizer, MODELS_DIR / "vectorizer.pkl")
    joblib.dump(classifier, MODELS_DIR / "classifier.pkl")
    log.info("✨ 模型訓練與匯出完成！")

if __name__ == "__main__":
    main()