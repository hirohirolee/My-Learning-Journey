"""
ingest.py — 地端合規知識庫向量化引擎
功能：讀取 ISO / SOP 文件 → 切片 → 嵌入向量 → 存入 ChromaDB
"""

import os
import json
import chromadb
from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from chromadb.utils import embedding_functions
import logging

# ── 日誌設定 ────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
log = logging.getLogger(__name__)

# ── 常數設定 ────────────────────────────────────────────────
DB_PATH       = "./audit_db"
COLLECTION    = "compliance_rules"
DOCS_PATH     = "./docs"          # 放置 PDF / TXT 來源文件的資料夾
CHUNK_SIZE    = 400
CHUNK_OVERLAP = 60

# 使用本地 Ollama 嵌入（不依賴外部 API）
EMBED_MODEL   = "nomic-embed-text"
OLLAMA_URL    = "http://localhost:11434"


# ── 內建示範知識庫（若 docs/ 為空則使用此處模擬資料）────────
DEMO_DOCUMENTS = {
    "iso14064_carbon": """
    ISO 14064-1 醫療感測器產線碳排放強度規範
    ─────────────────────────────────────────
    第 4.2 條：製造強度上限
    醫療感測器封裝產線之碳排放強度（Carbon Intensity）上限為 1.0 kgCO₂e/unit。
    超標即觸發 Level-1 通報，須在 2 小時內提交初步 CAPA 評估。
    累積超標 3 次以上，升為 Level-2，須在 24 小時內完成全線停工稽核。

    第 5.1 條：量測標準
    碳強度 = (直接排放 + 間接能耗排放) / 合格品產出數量
    計算週期：每班次（8 小時）核算一次，並寫入 MES 系統日誌。

    第 6.3 條：數據保存
    所有碳排放原始紀錄需本地留存 7 年，且不得單向傳輸至境外伺服器。
    """,

    "iso27001_security": """
    ISO 27001:2022 資訊安全管理規範（製造業適用版）
    ─────────────────────────────────────────────
    附件 A.8.16：異常活動偵測
    以下情況判定為重大資安事件，須立即觸發事件回應流程：
    1. 深夜（23:00-06:00）期間，單一帳號連續下載合規清冊超過 50 份。
    2. 境外 IP 嘗試存取內部 MES 或 ERP 系統。
    3. 特權帳號在非工作時段登入並修改生產參數。

    附件 A.5.24：事件回應程序
    - 發現後 15 分鐘內：隔離異常帳號，記錄觸發日誌。
    - 發現後 1 小時內：通報資安長（CISO）與法遵長（CCO）。
    - 發現後 4 小時內：提交初步事件報告。

    附件 A.8.7：日誌留存
    所有安全事件日誌須以加密格式儲存，保留 3 年，且需有完整性校驗機制。
    """,

    "sop_production": """
    生產管制調度標準作業程序（SOP-PROD-001）
    ─────────────────────────────────────────
    3.2 製程異常處理流程
    當以下任一條件成立，啟動異常處理程序：
    a. 碳排放強度超過 ISO 14064-1 規定上限
    b. 良率低於當班目標值 85%
    c. 設備 OEE 連續 2 小時低於 65%

    3.3 CAPA 提交時限
    - 輕微異常（Level-1）：4 小時內提交矯正預防報告
    - 嚴重異常（Level-2）：1 小時內提交初步評估，24 小時內完成根因分析
    - 緊急停線（Level-3）：即時通報廠長，並同步觸發 ISO 27001 資安稽核

    3.4 交班紀錄要求
    每班組長須在交班前 30 分鐘完成以下項目：
    - 產出數量核對
    - 碳強度數值歸檔
    - 異常事件紀錄（若有）
    - 設備點檢清單簽核

    3.5 資料存取控制
    MES 系統資料下載需有班長級以上授權，且每次下載均自動記錄日誌。
    """,

    "capa_template": """
    矯正預防措施報告（CAPA）標準模板說明
    ─────────────────────────────────────
    CAPA 報告必填欄位：
    1. 事件描述：何時、何地、何人、何事（5W1H）
    2. 直接原因：導致此次異常的直接觸發因素
    3. 根本原因：Root Cause Analysis（建議使用魚骨圖或 5-Why 分析法）
    4. 矯正措施（Corrective Action）：立即採取的糾正行動，含負責人與完成時限
    5. 預防措施（Preventive Action）：防止復發的長期改善方案
    6. 效果驗證：改善措施施行後的成效追蹤方式與指標
    7. 審核簽核：直屬主管與品保主管必須在 48 小時內完成審核簽核

    根因分析指引：
    - 人（Man）：操作者技能、訓練充分性
    - 機（Machine）：設備精度、保養狀態
    - 料（Material）：原料品質、供應商管控
    - 法（Method）：作業方法、SOP 適切性
    - 環（Environment）：溫溼度、潔淨度
    """
}


def get_embedding_function():
    """建立本地 Ollama 嵌入函式（不依賴 OpenAI 等外部服務）"""
    try:
        ef = embedding_functions.OllamaEmbeddingFunction(
            url=f"{OLLAMA_URL}/api/embeddings",
            model_name=EMBED_MODEL
        )
        log.info(f"✅ 嵌入模型載入成功：{EMBED_MODEL}")
        return ef
    except Exception as e:
        log.warning(f"⚠️  Ollama 嵌入不可用，改用預設嵌入函式：{e}")
        return embedding_functions.DefaultEmbeddingFunction()


def load_documents_from_folder(folder: str) -> dict:
    """從 docs/ 資料夾讀取 PDF 與 TXT 文件"""
    docs = {}
    path = Path(folder)
    if not path.exists():
        log.warning(f"📂 文件資料夾不存在：{folder}，使用內建示範資料")
        return {}

    for file in path.iterdir():
        try:
            if file.suffix.lower() == ".pdf":
                loader = PyPDFLoader(str(file))
                pages = loader.load()
                docs[file.stem] = "\n".join(p.page_content for p in pages)
                log.info(f"📄 已載入 PDF：{file.name}（{len(pages)} 頁）")
            elif file.suffix.lower() == ".txt":
                loader = TextLoader(str(file), encoding="utf-8")
                pages = loader.load()
                docs[file.stem] = pages[0].page_content
                log.info(f"📄 已載入 TXT：{file.name}")
        except Exception as e:
            log.error(f"❌ 載入失敗 {file.name}：{e}")

    return docs


def ingest(reset: bool = False):
    """主流程：切片 → 向量化 → 寫入 ChromaDB"""
    log.info("=" * 55)
    log.info("🚀 啟動地端合規知識庫向量化流程")
    log.info("=" * 55)

    # 1. 初始化向量資料庫
    client = chromadb.PersistentClient(path=DB_PATH)
    ef = get_embedding_function()

    if reset:
        try:
            client.delete_collection(COLLECTION)
            log.info("🗑️  舊有知識庫已清除，重新建立中...")
        except Exception:
            pass

    collection = client.get_or_create_collection(
        name=COLLECTION,
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"}
    )

    # 2. 載入文件（優先使用外部文件，否則使用示範資料）
    external_docs = load_documents_from_folder(DOCS_PATH)
    all_docs = {**DEMO_DOCUMENTS, **external_docs}
    log.info(f"📚 共載入 {len(all_docs)} 份文件待向量化")

    # 3. 切片
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", "。", "，", " ", ""]
    )

    # 4. 批次寫入
    total_chunks = 0
    for doc_id, text in all_docs.items():
        chunks = splitter.split_text(text.strip())
        if not chunks:
            continue

        ids       = [f"{doc_id}_{i}" for i in range(len(chunks))]
        metadatas = [{"source": doc_id, "chunk_index": i} for i in range(len(chunks))]

        # 避免重複寫入
        existing = collection.get(ids=ids)["ids"]
        new_ids, new_docs, new_metas = [], [], []
        for cid, chunk, meta in zip(ids, chunks, metadatas):
            if cid not in existing:
                new_ids.append(cid)
                new_docs.append(chunk)
                new_metas.append(meta)

        if new_ids:
            collection.add(documents=new_docs, metadatas=new_metas, ids=new_ids)
            log.info(f"  ✅ {doc_id}：新增 {len(new_ids)} 個向量片段")
        else:
            log.info(f"  ⏭️  {doc_id}：已是最新，略過")

        total_chunks += len(chunks)

    log.info("=" * 55)
    log.info(f"🏁 向量化完成！總片段數：{total_chunks}，存放於：{DB_PATH}/")
    log.info("=" * 55)

    # 5. 輸出摘要 JSON
    summary = {
        "total_documents": len(all_docs),
        "total_chunks": total_chunks,
        "db_path": DB_PATH,
        "collection": COLLECTION,
        "documents": list(all_docs.keys())
    }
    with open("ingest_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    log.info("📋 摘要已輸出至 ingest_summary.json")

    return summary


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="合規知識庫向量化工具")
    parser.add_argument("--reset", action="store_true", help="清除舊資料，重新向量化")
    args = parser.parse_args()
    ingest(reset=args.reset)
