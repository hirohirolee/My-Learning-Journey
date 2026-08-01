import streamlit as st

import os
import chromadb
from chromadb.utils import embedding_functions
from typing import List

DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chroma_db")
COLLECTION_NAME = "iso_knowledge"

# 初始化 Embedding 函數：自動容錯降級機制
try:
    # 優先嘗試載入輕量化多語言/中文 Embedding 模型 (若安裝有 sentence-transformers 則會使用)
    embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )
    # 測試一下是否能用，避免 Lazy Load 時在執行中出錯
    embedding_fn(["測試"])
except Exception:
    # Fallback 降級到 ChromaDB 預設的內建輕量級 ONNX 嵌入模型 (不依賴 PyTorch，最適合地端資源受限運行)
    embedding_fn = embedding_functions.DefaultEmbeddingFunction()

def get_chroma_client():
    return chromadb.PersistentClient(path=DB_DIR)

def init_rag_db():
    """初始化/獲取 ChromaDB 的 Collection"""
    client = get_chroma_client()
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_fn
    )
    return collection

def import_iso_document(file_path: str) -> bool:
    """
    文件匯入與切片 (Ingestion Script)
    ──────────────────────────────────────────
    規則：使用 Chunk Size 600 字, Overlap 100 字進行切片，並寫入 ChromaDB
    """
    if not os.path.exists(file_path):
        st.write(f"[WARNING] 找不到條文檔案：{file_path}")
        return False
        
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()
        
    chunk_size = 600
    overlap = 100
    chunks = []
    
    # 滑動窗口切片
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        # 若已讀到結尾，中斷
        if end >= len(text):
            break
        start += (chunk_size - overlap)
        
    if not chunks:
        return False
        
    collection = init_rag_db()
    
    ids = [f"doc_{os.path.basename(file_path)}_{i}" for i in range(len(chunks))]
    metadatas = [{"source": os.path.basename(file_path)} for _ in range(len(chunks))]
    
    # 寫入向量資料庫
    collection.add(
        documents=chunks,
        metadatas=metadatas,
        ids=ids
    )
    st.write(f"[OK] 成功匯入文件 {file_path}，共切為 {len(chunks)} 片段存入向量庫。")
    return True

def query_knowledge(prompt: str, n_results: int = 3) -> str:
    """
    向量庫檢索：輸入 Prompt 檢索出最相關的前 n_results 筆 ISO 條文
    """
    try:
        collection = init_rag_db()
        results = collection.query(
            query_texts=[prompt],
            n_results=n_results
        )
        documents = results.get("documents", [[]])[0]
        if not documents:
            return "無相關參考法規條文。"
        # 將取得的文件片段組合成 context 文本
        return "\n\n---\n\n".join(documents)
    except Exception as e:
        st.write(f"[WARNING] 檢索知識庫失敗: {e}")
        return "無相關參考法規條文 (檢索系統異常)。"

def init_mock_data():
    """
    初始化並導入 Mock ISO 條文知識庫（開箱即用）。
    知識庫涵蓋：
      - ISO 27001 資訊安全事件管理
      - ISO 14064-1 溫室氣體盤查（ESG 深度擴充，Step 5 新增）
      - SOP-PROD-001 生產管理
    若向量庫中文件數量不足（< 預期片段數），會強制重建以套用最新知識庫內容。
    """
    # ── 預期的最低片段數門檻（新增 ESG 知識後應有更多片段）────────
    EXPECTED_MIN_CHUNKS = 8

    try:
        client = get_chroma_client()
        collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=embedding_fn
        )
        current_count = collection.count()

        # 若向量庫已有足夠的片段，跳過（避免重複導入）
        if current_count >= EXPECTED_MIN_CHUNKS:
            st.write(f"[OK] 向量知識庫已就緒（現有 {current_count} 片段，門檻 {EXPECTED_MIN_CHUNKS}），跳過重建。")
            return

        # 若片段不足（首次啟動或知識庫升級後），清空後重新導入
        if current_count > 0:
            st.write(f"[INFO] 向量知識庫片段數 ({current_count}) 低於門檻，正在重建以套用最新 ESG 知識庫...")
            client.delete_collection(name=COLLECTION_NAME)
            collection = client.get_or_create_collection(
                name=COLLECTION_NAME,
                embedding_function=embedding_fn
            )

        mock_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mock_iso_rules.txt")

        # ══════════════════════════════════════════════════════════
        # 知識庫文本：覆蓋 ISO 14064-1（深度 ESG）、ISO 27001、SOP
        # ══════════════════════════════════════════════════════════
        mock_text = (
            # ── 區塊 A：ISO 27001 資訊安全 ──────────────────────────
            "【ISO 27001 A.8.16 資訊安全事件管理與審計】\n"
            "組織應建立深夜或異常時段大量下載之偵測機制。若研發伺服器或合規資產遭受連續海外登入嘗試，"
            "隨後有高容量敏感數據（例如專利代碼或合規清冊）遭異常下載導出，應判定為重大資安威脅。"
            "安全主管應採取防禦手段，包括對來源 IP 進行網路阻斷、立即隔離/停用該可疑帳號，"
            "並重置該帳號的單一登入 (SSO) 憑證/登入 Token，同時於 2 小時內向 CISO 申報。\n\n"

            # ── 區塊 B：SOP 生產管理 ────────────────────────────────
            "【SOP-PROD-001 生產管理與良率改善防呆對策】\n"
            "在各班別生產運作期間，當班良率目標應維持在 85.0% 以上。若良率低於此合規閾值，"
            "製程組長與品保工程師應於 4 小時內草擬矯正預防措施 (CAPA) 報告。"
            "排查重點應包含 SMT 貼片機之吸嘴磨損狀態檢測、回焊爐加熱區溫度設定校準，"
            "並立即啟動設備防呆防錯校正程序。\n\n"

            # ══════════════════════════════════════════════════════
            # [Step 5 ESG 擴充] ISO 14064-1 溫室氣體盤查深度知識庫
            # ══════════════════════════════════════════════════════

            # ── 區塊 C：碳排放強度合規門檻與預警等級 ───────────────
            "【ISO 14064-1 §5.2 組織溫室氣體排放邊界設定與碳強度預警等級】\n"
            "企業應依 ISO 14064-1 §5.2 設定組織邊界，明確界定直接排放（範疇一）與間接排放（範疇二）的責任廠區範圍。"
            "碳排放強度（Carbon Intensity，CI）以每單位產品碳排量計，單位為 kgCO₂e/unit，法定合規上限為 1.0 kgCO₂e/unit。\n"
            "預警等級定義：\n"
            "  Level-1（輕微預警）：CI 超過 1.0 且小於 1.5 kgCO₂e/unit → 啟動內部改善追蹤，通知部門主管，4 小時內提交改善計畫。\n"
            "  Level-2（嚴重超標）：CI 達 1.5 以上且小於 2.0 kgCO₂e/unit → 立即向永續發展委員會提交矯正報告，納入月度 ESG 檢討會議。\n"
            "  Level-3（緊急停線評估）：CI 達 2.0 kgCO₂e/unit 以上 → 通報廠長，召開跨部門減碳緊急會議，評估停線或限產措施。\n\n"

            # ── 區塊 D：範疇一（直接排放）異常查核要點 ─────────────
            "【ISO 14064-1 §5.3 範疇一（Scope 1）直接排放異常查核點】\n"
            "範疇一（Scope 1）直接排放包含：廠區自有燃燒設備（鍋爐、工業加熱爐）、製程逸散（冷媒洩漏、溶劑揮發）、"
            "自有車輛移動源排放。異常查核要點：\n"
            "  1. 燃料消耗量（天然氣/柴油）是否與產量比例相符；若能耗強度異常上升，應排查燃燒效率衰退或設備洩漏。\n"
            "  2. 製程冷媒（HFCs）年度使用量是否超出基準線 15%，若是則需盤查冷媒系統密封性並更新排放係數。\n"
            "  3. 活動數據（Activity Data）量測異常：計量設備讀數中斷、數據缺漏件數超過 3 筆/月，應立即啟動數據補填程序，\n"
            "     並在盤查報告中標注「估算值」與不確定性百分比（建議 < ±5%）。\n\n"

            # ── 區塊 E：範疇二（間接排放）異常查核要點 ─────────────
            "【ISO 14064-1 §5.4 範疇二（Scope 2）間接排放異常查核與能耗數據管理】\n"
            "範疇二（Scope 2）間接排放主要來源為購買電力、熱能或蒸汽。查核關鍵事項：\n"
            "  1. 電力消耗數據傳輸完整性：若 MES 或能源管理系統偵測到設備能耗數據傳輸中斷（如 SMT 設備、空壓機群、空調系統），"
            "     當日能耗數據應以「估算值」方式填補，並於 24 小時內完成數據修復，否則影響範疇二排放量計算的準確性，"
            "     導致年度 GHG 盤查報告不符合 ISO 14064-1 §7.4 數據品質要求。\n"
            "  2. 電網排放係數（Grid Emission Factor，GEF）應每年更新；若使用過期係數，盤查結果可能低估實際排放量。\n"
            "  3. 再生能源憑證（REC/Green Power）應在盤查系統中正確抵減，避免重複計算。\n\n"

            # ── 區塊 F：數據品質管理 (DQM) ────────────────────────
            "【ISO 14064-1 §7.4 數據品質管理（DQM）與不確定性分析】\n"
            "為確保 GHG 盤查報告的完整性與可信度，組織應執行以下數據品質管理（DQM）措施：\n"
            "  1. 數據完整性檢查：每月核查所有排放源的活動數據是否完整，缺漏率應低於 1%；超過時需提出數據缺漏矯正行動計畫。\n"
            "  2. 排放係數更新：直接排放係數（Emission Factor）至少每 3 年依 IPCC 指引或主管機關公告更新；"
            "     若發現係數誤差超過 ±10%，應重新計算當期排放量並提出差異說明。\n"
            "  3. 不確定性評估：組織應對每個排放源進行不確定性評估（I 類或 II 類量化），"
            "     整體盤查不確定性目標為 ±5% 以內，超過者須在 GHG 聲明書中揭露風險說明。\n"
            "  4. 內部品質稽核：每年應針對至少 3 個高排放源進行交叉核查（Cross-Check），"
            "     比對設備計量數據、電費帳單、生產日報三方數據的一致性，差異超過 3% 應立即展開根因調查。\n\n"

            # ── 區塊 G：CAPA 矯正措施與減碳行動架構 ────────────────
            "【ISO 14064-1 §8 CAPA 矯正預防措施與減碳行動架構】\n"
            "當碳排放量超標或數據品質不符規範時，應啟動以下 CAPA 矯正預防架構：\n"
            "  矯正措施（短期，0-30 天）：\n"
            "    - 隔離超標排放設備，進行燃燒效率調整或設備維修。\n"
            "    - 修補能耗數據傳輸中斷，確保數據鏈路完整。\n"
            "    - 更換失效計量表具，並進行量測系統校驗（MSA 分析）。\n"
            "  預防措施（中期，1-3 個月）：\n"
            "    - 導入即時能耗監控看板（Energy Dashboard），設置閾值告警。\n"
            "    - 建立每日碳排放強度自動計算與異常推播機制。\n"
            "    - 對高排放製程設備排定年度預防保養計畫（PM Plan），降低突發性效率衰退風險。\n"
            "  系統性改善（長期，3-12 個月）：\n"
            "    - 規劃製程電氣化，降低範疇一直接排放比例。\n"
            "    - 採購再生能源或綠電憑證（REC），降低範疇二電力碳足跡。\n"
            "    - 導入 ISO 50001 能源管理系統，與 ISO 14064-1 盤查流程整合。\n\n"

            # ── 區塊 H：盤查報告揭露要求 ────────────────────────────
            "【ISO 14064-1 §9 GHG 盤查聲明書揭露要求與第三方查驗】\n"
            "組織的年度溫室氣體盤查聲明書（GHG Inventory Statement）應符合以下揭露要求：\n"
            "  1. 揭露項目：組織邊界說明、各範疇排放量（tCO₂e）、排放強度、基準年設定說明、數據品質說明。\n"
            "  2. 查驗等級：有意義性保證（Reasonable Assurance，RA）需第三方查驗機構進行實地稽核，"
            "     有限性保證（Limited Assurance，LA）則以書面審查為主；上市/上櫃公司建議採 RA 等級。\n"
            "  3. 重大性判定：單一排放源超過組織總排放量 5% 以上，應視為重大排放源，需獨立揭露，"
            "     並提出具體管控措施說明。"
        )

        with open(mock_file, "w", encoding="utf-8") as f:
            f.write(mock_text)

        import_iso_document(mock_file)
        st.write(f"[OK] ESG 知識庫（ISO 14064-1 深度擴充版）已成功寫入向量資料庫。")

    except Exception as e:
        st.write(f"[WARNING] 初始化 Mock 向量資料庫時出錯: {e}")


# ====== 自動生成的測試執行區塊 ======
if __name__ == "__main__":
    st.write("---")
    st.subheader("函數測試區塊")
    if st.button("執行 get_chroma_client"):
        try:
            res = get_chroma_client() # 請視需要自行補上參數
            st.write("執行結果:", res)
        except Exception as e:
            st.error(f"執行出錯，可能需要提供參數：{e}")
    if st.button("執行 init_rag_db"):
        try:
            res = init_rag_db() # 請視需要自行補上參數
            st.write("執行結果:", res)
        except Exception as e:
            st.error(f"執行出錯，可能需要提供參數：{e}")
    if st.button("執行 import_iso_document"):
        try:
            res = import_iso_document() # 請視需要自行補上參數
            st.write("執行結果:", res)
        except Exception as e:
            st.error(f"執行出錯，可能需要提供參數：{e}")
    if st.button("執行 query_knowledge"):
        try:
            res = query_knowledge() # 請視需要自行補上參數
            st.write("執行結果:", res)
        except Exception as e:
            st.error(f"執行出錯，可能需要提供參數：{e}")
    if st.button("執行 init_mock_data"):
        try:
            res = init_mock_data() # 請視需要自行補上參數
            st.write("執行結果:", res)
        except Exception as e:
            st.error(f"執行出錯，可能需要提供參數：{e}")
