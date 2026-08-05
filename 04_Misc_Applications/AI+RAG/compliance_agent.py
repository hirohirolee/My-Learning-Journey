import os
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# 設定本地向量資料庫儲存目錄
CHROMA_DB_DIR = "./chroma_db_store"

def setup_rag_system(txt_path="iso_14064_1_rules.txt"):
    """讀取條文、切割文本並建立 Chroma 向量資料庫"""
    print("[*] 正在初始化 RAG 向量知識庫...")
    
    if not os.path.exists(txt_path):
        print(f"[錯誤] 找不到法規檔案 {txt_path}")
        return None
        
    try:
        # 1. 載入法規文件
        loader = TextLoader(txt_path, encoding="utf-8")
        documents = loader.load()
        
        # 2. 字元切塊 (確保不會截斷關鍵句子，給定適當重疊)
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=150, chunk_overlap=30)
        docs = text_splitter.split_documents(documents)
        
        # 3. 初始化 Embedding 模型 (改用本地免費的 HuggingFace Sentence Transformers)
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        
        # 4. 存入 ChromaDB，並實例化持久化目錄
        vectorstore = Chroma.from_documents(
            documents=docs,
            embedding=embeddings,
            persist_directory=CHROMA_DB_DIR
        )
        print("[+] RAG 知識庫建立與索引完成！\n")
        return vectorstore
        
    except Exception as e:
        print(f"[錯誤] 建立向量資料庫時發生例外：{e}")
        return None

def generate_compliance_report(anomalies_json, vectorstore, groq_api_key):
    """接收異常 JSON，檢索最相關的法規條文，並透過 LLM 生成顧問報表"""
    print("[*] 啟動 AI 顧問代理人進行風險評估與報告生成...")
    
    try:
        # 建立檢索器，設定檢索前 2 筆最相關條塊
        retriever = vectorstore.as_retriever(search_kwargs={"k": 2})
        
        # 初始化 LLM 模型 (使用雲端 Groq Llama3)
        llm = ChatGroq(model="llama3-70b-8192", temperature=0.1, groq_api_key=groq_api_key)
        
        # 建立系統 Prompt 樣板
        system_prompt = (
            "你是一位擁有 18 年製造業現場經驗，且精通 ISO 14064-1 規範的「高階企業內控 AI 顧問」。\n"
            "當你收到【廠區異常數據 JSON】時，必須結合從【關聯法規條文】中取得的資訊，進行綜合判斷。\n"
            "請保持專業、冷靜、客觀的語氣。切勿包含多餘的問候語。請嚴格使用以下 Markdown 格式輸出報告：\n\n"
            "## 🔴 廠區數據異常預警通報\n"
            "*   **事件概述：** [簡述發生的產線與日期]\n"
            "*   **數據偏離分析：** [詳細說明實際用電量與基準的差異，並計算偏離幅度]\n\n"
            "## 📋 ISO 合規性風險評估\n"
            "*   **關聯法規條款：** [引用 Context 中提及的 ISO 條款與規範]\n"
            "*   **風險說明：** [解釋該數據若不處理將如何違反該法規，並點出稽核風險]\n\n"
            "## 🔍 潛在根因分析 (Root Cause Analysis)\n"
            "*   [提出第一個合理的現場設備/製程假設原因]\n"
            "*   [提出第二個可能的人為操作或數據傳輸錯誤假設]\n\n"
            "## 🛠️ 矯正與預防措施建議 (CAPA)\n"
            "*   **立即處置 (Immediate Action)：** [結合法規精神給出立即執行的動作]\n"
            "*   **長期預防 (Preventive Action)：** [給出未來系統或 SOP 優化建議]\n\n"
            "======================\n"
            "【關聯法規條文 (Context)】\n{context}\n\n"
            "【廠區異常數據 JSON】\n{anomalies}"
        )
        
        prompt = ChatPromptTemplate.from_template(system_prompt)
        
        # 定義格式化檢索結果的輔助函式
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)
            
        # 建立 LangChain LCEL 工作流 Pipeline
        rag_chain = (
            {"context": retriever | format_docs, "anomalies": RunnablePassthrough()}
            | prompt
            | llm
            | StrOutputParser()
        )
        
        print("[*] 正在透過 LLM 進行邏輯推理並撰寫報告 (可能需要幾秒鐘)...")
        report = rag_chain.invoke(anomalies_json)
        print("[+] 報告生成完成！\n")
        return report
        
    except Exception as e:
        print(f"[錯誤] AI 生成報告時發生例外：{e}")
        return None
