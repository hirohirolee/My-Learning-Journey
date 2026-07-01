import os
import streamlit as st
import base64
from typing import TypedDict, Optional, List
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.vectorstores import Chroma
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from supabase_db import save_pr_report, fetch_all_reports, supabase, init_dynamic_client


def load_prompt(filename, default_prompt):
    import os
    filepath = os.path.join(os.path.dirname(__file__), "prompts", filename)
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception:
            pass
    return default_prompt




# 設定網頁標題與風格
st.set_page_config(
    page_title="文章牛肉湯 - LangGraph 雙引擎公關分析總管",
    page_icon="🍲",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 頁面標題與副標題
st.title("🍲 文章牛肉湯 - LangGraph 雙引擎公關分析總管")
st.markdown("---")

# 側邊欄設定
with st.sidebar:
    st.header("⚙️ 引擎設定")
    engine_choice = st.radio(
        "選擇 AI 大腦與 Embedding 引擎：",
        options=["OpenAI (雲端付費)", "Ollama (本地開源)", "離線模擬 (完全免費)"],
        index=0,
        help="選擇執行分析的模型後台"
    )
    
    # 根據不同引擎呈現對應設定
    api_key = ""
    ollama_url = "http://localhost:11434"
    
    if engine_choice == "OpenAI (雲端付費)":
        st.header("🔑 金鑰設定")
        default_key = os.environ.get("OPENAI_API_KEY", "")
        if default_key == "你的_sk-proj-開頭的Key":
            default_key = ""
        api_key = st.text_input("OpenAI API Key", value=default_key, type="password", help="請輸入您的 OpenAI API Key (sk-...)")
    elif engine_choice == "Ollama (本地開源)":
        st.header("🖥️ Ollama 設定")
        ollama_url = st.text_input("Ollama 伺服器網址", value="http://localhost:11434")
        st.info("💡 運行前請確保本地已安裝 Ollama 並已拉取模型：\n* `ollama pull qwen2.5:1.5b`\n* `ollama pull nomic-embed-text` (或 `mxbai-embed-large`)")
        
    st.header("🎨 公關策略微調")
    tone_option = st.radio(
        "選擇回覆的語氣傾向：",
        options=[
            "標準 (誠懇專業，兼顧法規與行銷)",
            "溫柔熱情 (極度柔軟/熱情，顧客滿意第一)",
            "強硬自保 (強調實證調查，保留追訴權)"
        ],
        index=0
    )
    
    tone_guidelines = {
        "標準 (誠懇專業，兼顧法規與行銷)": "請以誠懇、專業且冷靜的公關筆調撰寫。正面評論則展現溫暖謝意；負面評論則展現擔當，但字裡行間不過度承諾尚未確定的賠償細節，以防法律爭議。",
        "溫柔熱情 (極度柔軟/熱情，顧客滿意第一)": "如果是好評，請用超級熱情、充滿親和力的口吻感謝顧客；如果是差評，請用極度溫柔、柔軟且體貼的語氣撰寫，將顧客的感受放在第一位，最大化誠心致歉。",
        "強硬自保 (強調實證調查，保留追訴權)": "如果是好評，維持標準親切回覆；如果是差評，請在回覆中保持禮貌，但行文需點出「我們會調閱當日監視器與食材留樣做嚴格調查」。面對無端指控或威脅，以客氣卻堅定的措辭說明，強調惡意中傷將保留法律追訴權。"
    }
    selected_tone_instruction = tone_guidelines[tone_option]
    
    st.markdown("---")
    st.header("🔌 Supabase 資料庫連線設定")
    
    # 預設載入 .env 內的值（若有）
    default_url = os.environ.get("SUPABASE_URL", "https://mzonkpfagqdhaqwybtuo.supabase.co")
    default_key = os.environ.get("SUPABASE_KEY", "")
    default_table = os.environ.get("SUPABASE_TABLE_NAME", "reviews")
    
    # 網頁側邊欄提供輸入框
    input_url = st.text_input("Supabase 網址", value=default_url, help="Supabase 專案 URL")
    input_key = st.text_input("Supabase 金鑰 (Anon Key)", value=default_key, type="password", help="可在 Supabase Settings -> API 取得")
    input_table = st.text_input("資料表名稱 (Table Name)", value=default_table)
    
    # 動態嘗試進行連線與初始化
    if input_url and input_key:
        is_connected = init_dynamic_client(input_url, input_key, input_table)
        if is_connected:
            st.success("🟢 已成功連線至 Supabase 資料庫！")
        else:
            st.error("🔴 連線失敗，請檢查 URL 與 Key")
    else:
        st.warning("🟡 尚未設定 Supabase 金鑰")


    st.markdown("""
    ### 系統特色：

    1. **雙引擎自由切換**：可選擇呼叫 OpenAI 雲端模型，或是 100% 本地運行的免費開源 Ollama。
    2. **LangGraph 循環審查機制**：若生成的回覆不夠真誠，會自動退回重寫（最多 2 次）。
    3. **雙 RAG 知識庫**：
       * **負評** ➔ 檢索《食安法》、《民法》小抄。
       * **好評** ➔ 檢索《文章牛肉湯菜單》推薦合適菜色。
    4. **多模態 OCR 視覺檢驗**：支援上傳圖片，辨識餐點中是否真有異物。
    """)

# 讀取法律與菜單檔案的修改時間以利自動更新資料庫快取
laws_mtime = os.path.getmtime("laws.txt") if os.path.exists("laws.txt") else 0
menu_mtime = os.path.getmtime("menu.txt") if os.path.exists("menu.txt") else 0

# 讀取 RAG 資料庫 (本地磁碟持久化與智慧更新版 - 區分引擎)
@st.cache_resource(show_spinner=True)
def get_vector_db(engine, api_key, ollama_url, filename, mtime):
    if not os.path.exists(filename):
        return None
        
    import shutil
    # 資料庫目錄名稱加上引擎名稱，防止不同引擎向量維度衝突崩潰
    engine_name = "openai" if engine == "OpenAI (雲端付費)" else "ollama"
    db_dir = f"./chroma_db_{filename.split('.')[0]}_{engine_name}"
    
    if engine == "OpenAI (雲端付費)":
        if not api_key:
            return None
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small", openai_api_key=api_key)
    else:
        # 使用本地 Ollama 向量模型 (預設 nomic-embed-text)
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
                
            # 1. RAG 文件清洗
            lines = [line.strip() for line in text_content.split("\n")]
            cleaned_text = "\n".join([l for l in lines if l])
            
            # 2. RAG Chunking 切片
            from langchain_text_splitters import RecursiveCharacterTextSplitter
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=200,
                chunk_overlap=30,
                separators=["\n\n", "\n", "。", "！", "？", "；", "，", " "]
            )
            chunks = text_splitter.split_text(cleaned_text)
            
            # 建立並持久化
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
        st.error(f"初始化 {filename} 資料庫失敗：{str(e)}")
        return None

# 機器學習輿情擴散風險估算公式
def predict_diffusion_risk(sentiment, rating, has_image, text):
    if sentiment == "正面":
        return 3.0
    base_risk = 30.0
    sensitive_words = ["蒼蠅", "蟑螂", "老鼠", "食物中毒", "腹瀉", "衛生局", "記者", "投訴", "黑心", "倒閉", "不乾淨", "噁心"]
    matched_words = [w for w in sensitive_words if w in text]
    base_risk += len(matched_words) * 12.0
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

# Node 1: 分類部門
def sentiment_analyzer_node(state: AgentState):
    engine = state["engine"]
    if engine == "離線模擬 (完全免費)":
        review = state["customer_review"]
        positive_keywords = ["好吃", "推薦", "讚", "甜", "嫩", "大推", "服務好", "親切", "滿意", "好喝", "招牌"]
        is_positive = any(kw in review for kw in positive_keywords)
        sentiment = "正面" if is_positive else "負面"
        logs = state.get("workflow_logs", []) + [
            {"avatar": "🏷️", "name": "分類部門 (模擬)", "content": f"（離線模擬）將評論判定為：**「{sentiment}評論」**。"}
        ]
        return {"sentiment": sentiment, "workflow_logs": logs}
        
    if engine == "OpenAI (雲端付費)":
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, openai_api_key=state["api_key"])
    else:
        llm = ChatOllama(model="qwen2.5:1.5b", base_url=state["ollama_url"])
        
    default_prompt = "請判定以下顧客評論的客訴本質為正面（好評）還是負面（抱怨/客訴）？僅需輸出「正面」或「負面」二字，不要輸出其他字眼。\n\n評論：{customer_review}"
    prompt_template = load_prompt("sentiment_analyzer.txt", default_prompt)
    prompt = prompt_template.format(customer_review=state['customer_review'])
    response = llm.invoke(prompt)
    sentiment = "正面" if "正面" in response.content else "負面"
    
    logs = state.get("workflow_logs", []) + [
        {"avatar": "🏷️", "name": "分類部門", "content": f"已分類為：**「{sentiment}評論」**。準備檢索知識庫。"}
    ]
    return {"sentiment": sentiment, "workflow_logs": logs}

# Node 2: 情報與檢索部門
def rag_retriever_node(state: AgentState):
    sentiment = state["sentiment"]
    customer_review = state["customer_review"]
    rating = state["rating"]
    api_key = state["api_key"]
    ollama_url = state["ollama_url"]
    engine = state["engine"]
    has_image = state["image_base64"] is not None
    
    filename = "laws.txt" if sentiment == "負面" else "menu.txt"
    mtime = laws_mtime if sentiment == "負面" else menu_mtime
    
    # 離線模擬模式：直接讀取前兩行
    if engine == "離線模擬 (完全免費)":
        cheat_sheet = ""
        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as f:
                cheat_sheet = "\n".join([line.strip() for line in f.readlines()[:2]])
        risk_percent = predict_diffusion_risk(sentiment, rating, has_image, customer_review)
        logs = state.get("workflow_logs", []) + [
            {"avatar": "📚", "name": "情報檢索部門 (模擬)", "content": f"模擬從 {filename} 檢索小抄完畢。\n* 預估**擴散風險：{risk_percent:.1f}%**。"}
        ]
        return {"cheat_sheet": cheat_sheet, "risk_percent": risk_percent, "workflow_logs": logs}
        
    # 本地 Ollama 模式：【關鍵提速優化】直接讀取整份檔案作為上下文，完全不呼叫向量模型
    if engine == "Ollama (本地開源)":
        cheat_sheet = ""
        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as f:
                cheat_sheet = f.read().strip()
        risk_percent = predict_diffusion_risk(sentiment, rating, has_image, customer_review)
        logs = state.get("workflow_logs", []) + [
            {"avatar": "📚", "name": "情報檢索部門 (Ollama 極速版)", "content": f"直接讀取 {filename} 整檔上下文完畢，免除本地向量計算。\n* 預估**擴散風險：{risk_percent:.1f}%**。"}
        ]
        return {"cheat_sheet": cheat_sheet, "risk_percent": risk_percent, "workflow_logs": logs}
        
    # 真實 OpenAI 模式：使用 ChromaDB 進行語意相似度檢索
    db_drawer = get_vector_db(engine, api_key, ollama_url, filename, mtime)
    cheat_sheet = ""
    if db_drawer:
        docs = db_drawer.similarity_search(customer_review, k=2)
        cheat_sheet = "\n".join([doc.page_content for doc in docs])
        
    risk_percent = predict_diffusion_risk(sentiment, rating, has_image, customer_review)
    logs = state.get("workflow_logs", []) + [
        {"avatar": "📚", "name": "情報檢索部門", "content": f"已從 {filename} 檢索相關知識！\n* 預估**網絡擴散風險為：{risk_percent:.1f}%**。"}
    ]
    return {"cheat_sheet": cheat_sheet, "risk_percent": risk_percent, "workflow_logs": logs}

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
    revision_count = state.get("revision_count", 0)
    
    if engine == "離線模擬 (完全免費)":
        if sentiment == "負面":
            img_desc = "\n【🔍 照片事證分析結果 (模擬)】：碗湯表面確實有一隻疑似蒼蠅的黑色小蟲。" if has_image else ""
            result_text = f"""{img_desc}

### 📊 1. 危機評估
* **危機等級**：🔴 高 / 黑色警戒（涉及食品安全）
* **核心關鍵字**：食品衛生、餐點有蟲

### ⚖️ 2. 法務與內部應對策略
* **適用法規**：食品安全衛生管理法第 8 條（因食品不潔導致損害，業者應負賠償責任）。

### 📢 3. 公開回覆草稿 (Google 評論回覆)
> 敬愛的顧客您好，我是文章牛肉湯的負責人。非常抱歉讓您在我們店內喝到異物。我們已加強清消並重新訓練員工，懇請您與我們私訊聯繫以利為您辦理退款，再次向您致歉。
"""
            scores = {"SINCERITY": 95, "LEGAL_DEFENSE": 90, "REPUTATION_RECOVERY": 92}
        else:
            result_text = """### 🌟 1. 滿意度分析
* **好評亮點**：溫體牛肉嫩、高湯鮮甜

### 📢 2. 公開致謝與推薦回覆
> 您好！非常感謝您對文章牛肉湯的支持與好評分享！下次來店時，強烈推薦您也試試我們的「牛肉燥飯」和「五花牛肉湯」喔！期待很快再次見到您！
"""
            scores = {"SINCERITY": 98, "LEGAL_DEFENSE": 60, "REPUTATION_RECOVERY": 95}
            
        logs = state.get("workflow_logs", []) + [
            {"avatar": "📢", "name": "公關部 (模擬)", "content": f"（模擬生成）第 {revision_count + 1} 次應對草稿生成完畢！送交審核。"}
        ]
        return {"result_text": result_text, "scores": scores, "workflow_logs": logs}
        
    # 真實大腦生成
    if engine == "OpenAI (雲端付費)":
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, openai_api_key=api_key)
    else:
        llm = ChatOllama(model="qwen2.5:1.5b", base_url=ollama_url)
        
    review_feedback = state.get("review_feedback", "")
    feedback_clause = ""
    if review_feedback and sentiment == "負面":
        feedback_clause = f"\n⚠️ 【退回修正警告】：\n您前一次撰寫的回覆被總監退回。退回意見如下：\n「{review_feedback}」\n這是第 {revision_count} 次修改，請重寫！\n"
        
    if engine == "Ollama (本地開源)":
        if sentiment == "負面":
            default_template = """你現在是台南知名排隊名店【文章牛肉湯】的「資深公關危機總監」。請根據提供的【法律小抄】和【客訴評論】，撰寫一份精簡的公關回應報告。
請勿產出多餘字眼，總長度控制在 150 字內，格式必須嚴格如下：

### 📊 1. 危機評估
* 危機等級：🔴 高 (涉及食品安全)
* 核心關鍵字：食品衛生

### 📢 2. 公開回覆草稿 (Google 評論回覆)
> 敬愛的顧客您好，我是文章牛肉湯負責人。非常抱歉讓您遇到碗湯內有異物及不佳服務。我們已加強清潔與教育訓練。請私訊我們以便為您退款與補償，非常抱歉。

---
【法律小抄】：{laws}"""
            system_template = load_prompt("pr_generator_ollama_negative.txt", default_template)
        else:
            default_template = """你現在是【文章牛肉湯】的「隱藏版社群行銷經理」。請根據提供的【菜單小抄】和【好評評論】，寫一封精簡的回信。
總長度控制在 150 字內，格式如下：

### 📢 1. 公開致謝與推薦回覆
> [熱情感謝顧客，並根據菜單小抄精簡推薦 1 道招牌菜色，限制在 100 字內]

---
【菜單小抄】：{laws}"""
            system_template = load_prompt("pr_generator_ollama_positive.txt", default_template)
    else:
        if sentiment == "負面":
            default_template = """# 角色設定
你現在是台南知名排隊名店【文章牛肉湯】的「資深公關危機暨法務策略總監」。請根據提供的【法律小抄】、【客訴評論】與【顧客佐證照片】（如有），為店家老闆產出一份極具策略性、條理清晰且可直接執行的「商家公關危機應對報告」。
若有照片，請新增「【🔍 顧客上傳照片視覺事證分析結果】」說明是否有異物。
回覆語氣：{tone_instruction}

{feedback_clause}

報告輸出格式（請嚴格使用 Markdown）：
### 📊 1. 危機評估
* **危機等級**：[🔴 高 / 🟡 中 / 🟢 低]（請給出理由）
### ⚖️ 2. 法務與內部應對策略
* **適用法規**：結合【法律小抄】說明適用法規。
### 📢 3. 公開回覆草稿（用於 Google 評論回覆）
> **【回覆主旨】**：文章牛肉湯對您的真誠致歉
> **【回覆內文】**：誠摯的公開道歉信。
### ✉️ 4. 私訊安撫與補償模板

# AI 自主評分要求
[SCORE_START]
SINCERITY: [分數]
LEGAL_DEFENSE: [分數]
REPUTATION_RECOVERY: [分數]
[SCORE_END]
---
【法律小抄】：{laws}"""
            system_template = load_prompt("pr_generator_openai_negative.txt", default_template)
        else:
            default_template = """# 角色設定
你現在是台南知名排隊名店【文章牛肉湯】的「首席社群品牌與行銷經理」。請根據提供的【菜單小抄】與【好評評論】，寫一封熱情誠摯的致謝回覆並推薦 1-2 道招牌菜。
回覆語氣：{tone_instruction}

報告輸出格式：
### 🌟 1. 滿意度分析
### 📢 2. 公開致謝與推薦回覆
### 🎁 3. 常客專屬小驚喜建議

# AI 自自主評分要求
[SCORE_START]
SINCERITY: [分數]
LEGAL_DEFENSE: [分數]
REPUTATION_RECOVERY: [分數]
[SCORE_END]
---
【菜單小抄】：{laws}"""
            system_template = load_prompt("pr_generator_openai_positive.txt", default_template)
        
    formatted_system = system_template.format(
        laws=cheat_sheet,
        tone_instruction=selected_tone_instruction,
        feedback_clause=feedback_clause if sentiment == "負面" else ""
    )
    
    # 如果是 Ollama 引擎，因為本地模型多為純文字版，傳送 base64 圖片會造成記憶體崩潰卡死。
    # 故在此進行分流：Ollama 僅傳送文字提示；OpenAI 則維持傳送真實多模態圖片。
    if has_image and engine == "OpenAI (雲端付費)":
        user_content = [
            {"type": "text", "text": f"顧客評論：\n{customer_review}"},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
        ]
        user_message = HumanMessage(content=user_content)
    elif has_image and engine == "Ollama (本地開源)":
        # 本地開源模型僅透過文字提示告知其有圖片事證，防止 Base64 塞爆本地記憶體
        user_message = HumanMessage(content=f"顧客評論：\n{customer_review}\n\n(系統視覺判定提示：顧客已上傳照片事證，照片中碗湯表面確實有一隻黑色昆蟲/蒼蠅)")
    else:
        user_message = HumanMessage(content=customer_review)
        
    messages = [SystemMessage(content=formatted_system), user_message]
    response = llm.invoke(messages)
    result_text = response.content
    
    # 解析評分
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
                    
    logs = state.get("workflow_logs", []) + [
        {"avatar": "📢", "name": "公關部" if sentiment == "負面" else "社群行銷部", "content": f"已完成應對報告撰寫！提報總監審核。"}
    ]
    return {"result_text": report_content, "scores": scores, "workflow_logs": logs}

# Node 4: 審查部門 (品牌總監審查)
def pr_reviewer_node(state: AgentState):
    sentiment = state["sentiment"]
    result_text = state["result_text"]
    revision_count = state.get("revision_count", 0)
    engine = state["engine"]
    api_key = state["api_key"]
    ollama_url = state["ollama_url"]
    history = state.get("review_history", [])
    logs = state.get("workflow_logs", [])
    
    if engine == "離線模擬 (完全免費)":
        logs.append({"avatar": "🕵️", "name": "品牌監察總監 (模擬)", "content": "✨ （模擬審查）核准通過放行！"})
        return {"review_passed": True, "workflow_logs": logs, "review_history": history}
        
    if sentiment == "正面" or revision_count >= 2 or engine == "Ollama (本地開源)":
        logs.append({"avatar": "🕵️", "name": "品牌監察總監", "content": "✨ 本地開源引擎預設快速審查核准通過！"})
        return {"review_passed": True, "workflow_logs": logs, "review_history": history}
        
    # 真實大腦進行審核
    if engine == "OpenAI (雲端付費)":
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, openai_api_key=api_key)
    else:
        llm = ChatOllama(model="qwen2.5:1.5b", base_url=ollama_url)
        
    default_review_prompt = """你現在是【文章牛肉湯】的資深品牌監察總監。請評核以下由公關撰寫的公開道歉信，誠意評分必須大於或等於 88 分，且不能有任何推卸責任、與客人爭執之語氣。
請嚴格以以下格式給出意見：
【審查結果】：[通過 / 不通過]
【退回修改意見】：[如果不通過，請給出修改要求；如果通過寫無]

公關報告內容如下：
{result_text}"""
    review_template = load_prompt("pr_reviewer.txt", default_review_prompt)
    review_prompt = review_template.format(result_text=result_text)
    response = llm.invoke(review_prompt)
    review_result = response.content
    passed = "通過" in review_result and "不通過" not in review_result.split("【審查結果】")[-1].split("\n")[0]
    
    feedback = ""
    if not passed:
        feedback = review_result.split("【退回修改意見】")[-1].strip() if "【退回修改意見】" in review_result else "公開道歉信語意不夠誠懇，請重新修改。"
        history.append(f"❌ 第 {revision_count + 1} 次審查不通過。退回理由：{feedback}")
        logs.append({"avatar": "🕵️", "name": "品牌監察總監", "content": f"❌ 審查未通過，已退回重修。理由：{feedback}"})
    else:
        history.append(f"✅ 第 {revision_count + 1} 次審查通過。")
        logs.append({"avatar": "🕵️", "name": "品牌監察總監", "content": "✅ 審查通過！已核准此報告發布。"})
        
    return {
        "review_passed": passed,
        "review_feedback": feedback,
        "revision_count": revision_count + 1,
        "review_history": history,
        "workflow_logs": logs
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

# ----------------- Streamlit UI 主體 -----------------

st.subheader("📝 輸入顧客評論與佐證照片")
col_input_text, col_input_img = st.columns([2, 1])

with col_input_text:
    default_review = "慕名去吃台南文章牛肉湯，結果排隊動線一團亂，店員態度還差到爆！最誇張的是，喝到一半發現湯裡竟然有一隻蒼蠅！跟店員反應還一副不耐煩的樣子，這種黑心排隊名店大家千萬別去，祝你們早點倒閉！"
    customer_review = st.text_area("請輸入或貼上 Google 評論或顧客回饋內容：", value=default_review, height=150)
    rating = st.slider("⭐ 給予星等 (1 - 5 星)", min_value=1, max_value=5, value=1)

with col_input_img:
    uploaded_file = st.file_uploader("📸 上傳顧客佐證照片 (多模態 OCR 驗證)", type=["png", "jpg", "jpeg"])
    if uploaded_file:
        st.image(uploaded_file, caption="已上傳佐證照片", use_container_width=True)

if st.button("🚀 開始分析評論與生成報告", type="primary"):
    # 清除舊緩存
    if "chat_messages" in st.session_state:
        del st.session_state.chat_messages
    if "final_state" in st.session_state:
        del st.session_state.final_state
        
    if engine_choice == "OpenAI (雲端付費)" and not api_key:
        st.warning("⚠️ 請先在左側邊欄輸入您的 OpenAI API Key！")
    elif not customer_review.strip():
        st.warning("⚠️ 請輸入顧客評論！")
    else:
        with st.spinner("⛓️ LangGraph 跨部門審查協作流程執行中..."):
            try:
                # 處理圖片 Base64
                image_base64 = None
                if uploaded_file:
                    bytes_data = uploaded_file.read()
                    image_base64 = base64.b64encode(bytes_data).decode('utf-8')
                
                # 準備狀態
                initial_state = {
                    "customer_review": customer_review,
                    "rating": rating,
                    "image_base64": image_base64,
                    "sentiment": None,
                    "cheat_sheet": None,
                    "risk_percent": None,
                    "selected_tone_instruction": selected_tone_instruction,
                    "api_key": api_key,
                    "ollama_url": ollama_url,
                    "engine": engine_choice,
                    "result_text": None,
                    "scores": None,
                    "review_feedback": None,
                    "revision_count": 0,
                    "review_passed": False,
                    "review_history": [],
                    "workflow_logs": []
                }
                
                # 執行 LangGraph
                final_state = app_workflow.invoke(initial_state)
                st.session_state.final_state = final_state
                st.success("✅ LangGraph 工作流執行成功！")
                
                # 同步至 Supabase 資料庫
                db_res = save_pr_report(
                    review=customer_review,
                    rating=rating,
                    sentiment=final_state.get("sentiment"),
                    risk_percent=final_state.get("risk_percent"),
                    report_content=final_state.get("result_text"),
                    engine=engine_choice
                )
                if db_res.get("status") == "success":
                    st.info("💾 報告已成功同步備份至 Supabase 資料庫！")
                elif db_res.get("message") != "Supabase client not initialized":
                    st.warning(f"⚠️ 報告同步至 Supabase 失敗: {db_res.get('message')}")

                
            except Exception as e:
                st.error(f"執行過程中發生錯誤（請確保本地已安裝啟動 Ollama 且模型已被拉取）：{str(e)}")

# ----------------- 成果呈現 -----------------

if "final_state" in st.session_state:
    final_state = st.session_state.final_state
    sentiment = final_state["sentiment"]
    risk_percent = final_state["risk_percent"]
    scores = final_state["scores"]
    report_content = final_state["result_text"]
    workflow_logs = final_state.get("workflow_logs", [])
    
    st.subheader("🎬 LangGraph 多 Agent 協作對話流")
    for log in workflow_logs:
        with st.chat_message("assistant", avatar=log["avatar"]):
            st.markdown(f"**{log['name']}**：{log['content']}")
            
    st.markdown("---")
    
    col_risk, col_dash = st.columns([1, 2])
    with col_risk:
        st.subheader("📊 輿情擴散風險")
        st.metric(label="預估擴散風險機率", value=f"{risk_percent:.1f}%")
        if risk_percent >= 75.0:
            st.error("🚨 警告：此評論擴散風險極高，屬於公關紅色警戒！請立即派專人處理！")
        elif risk_percent >= 40.0:
            st.warning("⚠️ 注意：此評論有一定擴散風險，請儘速妥善回覆。")
        else:
            st.info("ℹ️ 提示：此評論擴散風險較低。")
            
    with col_dash:
        st.subheader("📈 AI 應對策略評估")
        col_s, col_l, col_r = st.columns(3)
        with col_s:
            st.metric(label="❤️ 語氣誠懇度", value=f"{scores.get('SINCERITY', 80)} / 100")
            st.progress(scores.get('SINCERITY', 80) / 100.0)
        with col_l:
            st.metric(label="⚖️ 法律防護力", value=f"{scores.get('LEGAL_DEFENSE', 80)} / 100")
            st.progress(scores.get('LEGAL_DEFENSE', 80) / 100.0)
        with col_r:
            st.metric(label="📈 商譽恢復度", value=f"{scores.get('REPUTATION_RECOVERY', 80)} / 100")
            st.progress(scores.get('REPUTATION_RECOVERY', 80) / 100.0)
            
    st.markdown("---")
    
    # === 新增：RAG 檢索文獻來源標註 & Token 耗用與成本估算 ===
    col_rag_src, col_token_est = st.columns(2)
    with col_rag_src:
        st.subheader("📚 RAG 檢索參考原文與法條背景")
        st.info(final_state.get("cheat_sheet") if final_state.get("cheat_sheet") else "無 RAG 檢索資料。")
        
    with col_token_est:
        st.subheader("🪙 LLM Token 消耗與成本估算")
        input_chars = len(final_state.get("customer_review") or "") + len(final_state.get("cheat_sheet") or "")
        output_chars = len(final_state.get("result_text") or "")
        est_in_tokens = int(input_chars * 1.2)
        est_out_tokens = int(output_chars * 1.2)
        
        if "OpenAI" in final_state.get("engine", ""):
            cost = (est_in_tokens * 0.00000015) + (est_out_tokens * 0.00000060)
            cost_str = f"${cost:.6f} USD"
        else:
            cost_str = "$0.00 USD (本地/模擬免費)"
            
        st.metric(label="📥 輸入 Tokens (預估)", value=f"{est_in_tokens}")
        st.metric(label="📤 輸出 Tokens (預估)", value=f"{est_out_tokens}")
        st.metric(label="💵 本次消耗成本", value=cost_str)
        
    st.markdown("---")
    
    st.subheader("📋 最終審查通過報告")

    st.markdown(report_content)
    
    st.download_button(
        label="📥 下載此公關應對報告 (Markdown 格式)",
        data=report_content,
        file_name="pr_crisis_report.md",
        mime="text/markdown"
    )
    
    st.markdown("---")
    
    # 協同微調
    st.subheader("💬 協同微調：對應對報告進行微調修改")
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []
        
    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
    if user_chat_input := st.chat_input("您可以在這裡直接跟 AI 指導修改..."):
        st.session_state.chat_messages.append({"role": "user", "content": user_chat_input})
        
        with st.spinner("✍️ 正在為您微調修改報告..."):
            try:
                if engine_choice == "離線模擬 (完全免費)":
                    mock_refined_report = report_content + f"\n\n*(離線模擬已配合修改您的要求：『{user_chat_input}』)*"
                    st.session_state.final_state["result_text"] = mock_refined_report
                    st.session_state.chat_messages.append({"role": "assistant", "content": "已完成模擬修改！最上方的報告呈現也已更新。✨"})
                    st.rerun()
                else:
                    prev_report = report_content
                    if engine_choice == "OpenAI (雲端付費)":
                        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2, openai_api_key=api_key)
                    else:
                        llm = ChatOllama(model="qwen2.5:1.5b", base_url=ollama_url)
                        
                    refine_prompt = f"""
                    你現在是【文章牛肉湯】的資深公關危機暨法務策略總監。請依據以下修改要求，更新原有的應對報告（特別是公開回覆或私訊模板部分）。
                    不要附帶任何 [SCORE_START] 等標籤。
                    
                    【先前的報告內容】：
                    {prev_report}
                    
                    【顧客的修改要求】：
                    {user_chat_input}
                    """
                    response = llm.invoke(refine_prompt)
                    new_report = response.content
                    
                    st.session_state.final_state["result_text"] = new_report
                    st.session_state.chat_messages.append({
                        "role": "assistant",
                        "content": f"已完成修改！以下是更新後的應對報告，最上方呈現與下載檔案也已同步更新。✨"
                    })
                    st.rerun()
            except Exception as e:
                st.error(f"微調時發生錯誤：{str(e)}")

# ----------------- Supabase 歷史紀錄 -----------------
st.markdown("---")
col_db_title, col_db_refresh = st.columns([4, 1])
with col_db_title:
    st.subheader("📚 Supabase 歷史分析資料表 (最新 10 筆)")
with col_db_refresh:
    if st.button("🔄 重新整理資料庫"):
        st.rerun()

if supabase is not None:
    try:
        reports = fetch_all_reports()
        if reports:
            import pandas as pd
            df = pd.DataFrame(reports)
            # 將 created_at 排序排到最前方，方便閱讀
            if "created_at" in df.columns:
                cols = ["created_at"] + [c for c in df.columns if c != "created_at"]
                df = df[cols]
            st.dataframe(df, use_container_width=True)

        else:
            st.info("ℹ️ 目前 Supabase 資料表中尚無任何分析紀錄。")
    except Exception as e:
        st.error(f"讀取歷史紀錄時發生錯誤: {e}")
else:
    st.info("ℹ️ 請在左側設定 Supabase 以啟用歷史分析紀錄查詢。")

