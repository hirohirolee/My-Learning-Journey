"""
build_ml_pipeline.py
─────────────────────────────────────────────────────────────────────────────
ML 守門員訓練管線（第二段）

流程：
  1. 從 Supabase 撈取歷史輿情（欄位 `review`），支援筆數上限
  2. 以 LLM + PROMPT_STAGE_1 自動打標籤（0 / 1）
     - 批次處理 + sleep 做速率控制
     - 非 0/1 回傳 → 捨棄並 log，管線不中斷
     - 每 50 筆印出進度
  3. TfidfVectorizer 轉特徵 → train_test_split → RandomForestClassifier
     - class_weight="balanced" 處理樣本不平衡
     - 印出 accuracy / precision / recall / confusion_matrix
  4. joblib 匯出 model + vectorizer 至 ./models/

環境變數：
  SUPABASE_URL      必填（Supabase 專案 URL）
  SUPABASE_KEY      必填（Supabase anon/service key）
  SUPABASE_TABLE_NAME  選填，預設 "reviews"
  ENGINE            選填，"openai"（預設）或 "ollama"
  OPENAI_API_KEY    ENGINE=openai 時必填
  OLLAMA_BASE_URL   ENGINE=ollama 時選填，預設 http://localhost:11434
  OLLAMA_MODEL      ENGINE=ollama 時選填，預設 qwen2.5:3b
  MAX_RECORDS       選填，每次撈取筆數上限（整數），預設不限
  BATCH_SIZE        選填，每批 LLM 呼叫筆數，預設 10
  SLEEP_SECONDS     選填，每批間隔秒數，預設 1.0

執行方式：
  python build_ml_pipeline.py
─────────────────────────────────────────────────────────────────────────────
"""

import os
import sys
import time
import logging
import math
from pathlib import Path

# ── 0. 基本設定 ────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# 確保能找到同層模組
sys.path.append(str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

# 讀取環境變數（管線參數）
ENGINE          = os.environ.get("ENGINE", "openai").lower()
OPENAI_API_KEY  = os.environ.get("OPENAI_API_KEY", "")
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL    = os.environ.get("OLLAMA_MODEL", "qwen2.5:3b")
MAX_RECORDS_ENV = os.environ.get("MAX_RECORDS", "")
BATCH_SIZE      = int(os.environ.get("BATCH_SIZE", "10"))
SLEEP_SECONDS   = float(os.environ.get("SLEEP_SECONDS", "1.0"))
MODELS_DIR      = Path(__file__).parent / "models"

MAX_RECORDS: int | None = int(MAX_RECORDS_ENV) if MAX_RECORDS_ENV.strip().isdigit() else None

# ── 1. 撈取歷史資料 ────────────────────────────────────────────────────────

def fetch_reviews(max_records: int | None = None) -> list[dict]:
    """
    使用 supabase_db.fetch_all_reports() 撈取歷史評論。
    欄位 `review` 為原始輿情文字（第 1 段偵查確認）。
    """
    log.info("📡 連接 Supabase，撈取歷史評論資料...")
    from supabase_db import fetch_all_reports
    try:
        records = fetch_all_reports()
    except Exception as exc:
        log.error("❌ fetch_all_reports() 失敗：%s", exc)
        raise SystemExit(1)

    # 過濾：必須有非空的 review 欄位
    records = [r for r in records if r.get("review", "").strip()]

    if max_records is not None:
        records = records[:max_records]
        log.info("   套用筆數上限，取前 %d 筆", max_records)

    log.info("   共取得 %d 筆有效評論", len(records))
    return records


# ── 2. LLM 初始化 ──────────────────────────────────────────────────────────

def build_llm():
    """依 ENGINE 環境變數選擇 LLM，與 api_server.py 保持一致。"""
    if ENGINE == "ollama":
        from langchain_ollama import ChatOllama
        log.info("🤖 使用 Ollama 引擎：%s @ %s", OLLAMA_MODEL, OLLAMA_BASE_URL)
        return ChatOllama(model=OLLAMA_MODEL, base_url=OLLAMA_BASE_URL, temperature=0)
    else:
        if not OPENAI_API_KEY:
            log.error("❌ ENGINE=openai 但 OPENAI_API_KEY 未設定，請先設定環境變數。")
            raise SystemExit(1)
        from langchain_openai import ChatOpenAI
        log.info("🤖 使用 OpenAI 引擎：gpt-4o-mini")
        return ChatOpenAI(model="gpt-4o-mini", temperature=0, openai_api_key=OPENAI_API_KEY)


# ── 3. LLM 自動打標籤 ──────────────────────────────────────────────────────

def label_with_llm(reviews: list[str], llm) -> tuple[list[str], list[int]]:
    """
    逐批呼叫 LLM 對評論做 0/1 分類。

    - BATCH_SIZE  控制每批筆數（速率限制）
    - SLEEP_SECONDS 為批次間 sleep 秒數
    - 非 0/1 回傳 → log 並捨棄（不加入訓練集）
    - 每 50 筆印出進度

    回傳：
        kept_texts   合法標籤的評論文字 list
        kept_labels  對應的 0/1 標籤 list
    """
    from prompts.ml_prompts import PROMPT_STAGE_1

    kept_texts: list[str] = []
    kept_labels: list[int] = []
    discard_count = 0
    total = len(reviews)
    batches = math.ceil(total / BATCH_SIZE)

    log.info("🏷️  開始 LLM 自動打標籤（共 %d 筆，批次大小 %d，批次間 sleep %.1fs）",
             total, BATCH_SIZE, SLEEP_SECONDS)

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
                log.warning("   [#%d] LLM 呼叫失敗，捨棄。原因：%s", i, exc)
                discard_count += 1
                continue

            # 嚴格驗證：只接受單一字元 "0" 或 "1"
            if raw not in ("0", "1"):
                log.warning('   [#%d] 非法回傳（"%s"），捨棄。原文：%.60s', i, raw, text)
                discard_count += 1
                continue

            kept_texts.append(text)
            kept_labels.append(int(raw))

            # 每 50 筆進度報告
            if i % 50 == 0:
                log.info("   進度 %d / %d（保留 %d 筆，捨棄 %d 筆）",
                         i, total, len(kept_texts), discard_count)

        # 批次結尾 sleep（最後一批不 sleep）
        if batch_idx < batches - 1:
            time.sleep(SLEEP_SECONDS)

    log.info("✅ 打標完成：保留 %d 筆，捨棄 %d 筆（總計 %d 筆）",
             len(kept_texts), discard_count, total)
    return kept_texts, kept_labels


# ── 4. 訓練 ML 模型 ────────────────────────────────────────────────────────

def train_model(texts: list[str], labels: list[int]):
    """
    TfidfVectorizer → train_test_split → RandomForestClassifier。
    回傳 (vectorizer, classifier, metrics_dict)。
    """
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import (
        accuracy_score, precision_score, recall_score,
        confusion_matrix, classification_report
    )

    if len(texts) < 10:
        log.error("❌ 有效樣本不足（僅 %d 筆），無法訓練，請先確認 Supabase 資料量。", len(texts))
        raise SystemExit(1)

    log.info("⚙️  特徵工程：TfidfVectorizer（analyzer=char_wb, ngram=(2,4)）")
    vectorizer = TfidfVectorizer(
        analyzer="char_wb",     # 字元 n-gram，對中文效果優於 word
        ngram_range=(2, 4),
        max_features=20_000,
        sublinear_tf=True,
    )

    X = vectorizer.fit_transform(texts)
    y = labels

    pos = sum(y)
    neg = len(y) - pos
    log.info("   樣本分佈 → 正例(1)：%d，負例(0)：%d", pos, neg)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    log.info("   訓練集 %d 筆 / 驗證集 %d 筆", X_train.shape[0], X_test.shape[0])

    log.info("🌲 訓練 RandomForestClassifier（n_estimators=200, class_weight=balanced）")
    clf = RandomForestClassifier(
        n_estimators=200,
        max_depth=None,
        class_weight="balanced",   # 處理樣本不平衡
        random_state=42,
        n_jobs=-1,
    )
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)

    acc  = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, zero_division=0)
    rec  = recall_score(y_test, y_pred, zero_division=0)
    cm   = confusion_matrix(y_test, y_pred)

    print("\n" + "=" * 55)
    print("📊  訓練結果")
    print("=" * 55)
    print(f"  Accuracy  : {acc:.4f}  ({acc*100:.2f}%)")
    print(f"  Precision : {prec:.4f}")
    print(f"  Recall    : {rec:.4f}")
    print(f"  Confusion Matrix (row=真實, col=預測):")
    print(f"              Pred 0   Pred 1")
    print(f"    Actual 0   {cm[0,0]:5d}    {cm[0,1]:5d}")
    print(f"    Actual 1   {cm[1,0]:5d}    {cm[1,1]:5d}")
    print()
    print(classification_report(y_test, y_pred, target_names=["無關(0)", "危機(1)"]))
    print("=" * 55 + "\n")

    metrics = {
        "accuracy": acc,
        "precision": prec,
        "recall": rec,
        "confusion_matrix": cm.tolist(),
        "train_size": X_train.shape[0],
        "test_size": X_test.shape[0],
    }
    return vectorizer, clf, metrics


# ── 5. 匯出模型 ────────────────────────────────────────────────────────────

def export_models(vectorizer, classifier, models_dir: Path):
    """joblib 匯出至 ./models/，資料夾不存在時自動建立。"""
    import joblib

    models_dir.mkdir(parents=True, exist_ok=True)

    vec_path = models_dir / "vectorizer.pkl"
    clf_path = models_dir / "classifier.pkl"

    joblib.dump(vectorizer, vec_path)
    joblib.dump(classifier, clf_path)

    log.info("💾 模型已匯出：")
    log.info("   vectorizer → %s", vec_path)
    log.info("   classifier → %s", clf_path)


# ── 6. 主程式 ──────────────────────────────────────────────────────────────

def main():
    print("\n" + "=" * 55)
    print("🚀 ML 守門員訓練管線啟動")
    print(f"   ENGINE      = {ENGINE.upper()}")
    print(f"   MAX_RECORDS = {MAX_RECORDS if MAX_RECORDS else '不限'}")
    print(f"   BATCH_SIZE  = {BATCH_SIZE}")
    print(f"   SLEEP_SECS  = {SLEEP_SECONDS}")
    print("=" * 55 + "\n")

    # Step 1: 撈資料
    records = fetch_reviews(MAX_RECORDS)
    raw_texts = [r["review"] for r in records]

    # Step 2: 建 LLM + 打標籤
    llm = build_llm()
    texts, labels = label_with_llm(raw_texts, llm)

    if not texts:
        log.error("❌ 無任何有效標籤資料，管線終止。請檢查 LLM 回傳內容或資料來源。")
        raise SystemExit(1)

    # Step 3: 訓練
    vectorizer, classifier, metrics = train_model(texts, labels)

    # Step 4: 匯出
    export_models(vectorizer, classifier, MODELS_DIR)

    print("\n✨ 管線完成！")
    print(f"   Accuracy : {metrics['accuracy']*100:.2f}%")
    print(f"   Precision: {metrics['precision']*100:.2f}%")
    print(f"   Recall   : {metrics['recall']*100:.2f}%")
    print(f"   模型路徑  : {MODELS_DIR.resolve()}")


if __name__ == "__main__":
    main()
