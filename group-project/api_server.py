import os
import base64
import shutil
from typing import TypedDict, Optional, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.vectorstores import Chroma
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from supabase_db import save_pr_report


# 初始化 FastAPI 應用程式
app = FastAPI(
    title="文章牛肉湯 AI 雙引擎公關與社群分析 API 伺服器",
    description="提供前後端同學對接的 REST API。支援 OpenAI 雲端模型與本地 Ollama 模型動態雙引擎切換。",
    version="1.1.0"
)

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
    mock_mode: bool
    few_shot_examples: Optional[str]
    query_embedding: Optional[list]

# Node 1: 分類部門
def sentiment_analyzer_node(state: AgentState):
    if state["mock_mode"]:
        review = state["customer_review"]
        positive_keywords = ["好吃", "推薦", "讚", "甜", "嫩", "大推", "服務好", "親切", "滿意", "好喝", "招牌"]
        is_positive = any(kw in review for kw in positive_keywords)
        sentiment = "正面" if is_positive else "負面"
        return {"sentiment": sentiment}
        
    engine = state["engine"]
    if engine == "openai":
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, openai_api_key=state["api_key"])
    else:
        llm = ChatOllama(model="qwen2.5:3b", base_url=state["ollama_url"])
        
    prompt = f"請判定以下顧客評論的客訴本質為正面（好評）還是負面（抱怨/客訴）？僅需輸出「正面」或「負面」二字，不要輸出其他字眼。\n\n評論：{state['customer_review']}"
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
    
    filename = "laws.txt" if sentiment == "負面" else "menu.txt"
    mtime = laws_mtime if sentiment == "負面" else menu_mtime
    
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
        few_shot_examples = ""
        query_embedding = None
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
        llm = ChatOllama(model="qwen2.5:3b", base_url=ollama_url)
        
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
            > 敬愛的顧客您好，我是文章牛肉湯負責人。非常抱歉讓您遇到碗湯內有異物及不佳服務。我們已加強清潔與教育訓練。請私訊我們以便為您退款與補償，非常抱歉。
            
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

# ----------------- FastAPI Pydantic 模型定義 -----------------

class AnalyzeRequest(BaseModel):
    review: str
    rating: int = 1
    image_base64: Optional[str] = None
    tone: str = "標準"  # 標準, 溫柔熱情, 強硬自保
    engine: str = "openai"  # openai, ollama
    mock_mode: bool = False

# ----------------- REST API 接口實作 -----------------

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
        
        final_state = app_workflow.invoke(initial_state)
        
        # 同步至 Supabase 資料庫
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

@app.get("/api/health")
def health_check():
    return {"status": "ok", "api_key_configured": bool(os.environ.get("OPENAI_API_KEY"))}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
