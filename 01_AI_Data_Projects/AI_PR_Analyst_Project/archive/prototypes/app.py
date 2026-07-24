import os
import shutil
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.vectorstores import Chroma
from langchain_core.messages import HumanMessage, SystemMessage

# 1. 載入環境變數與金鑰設定
load_dotenv()

print("\n" + "="*50)
print("🍲 文章牛肉湯 - AI 互動式公關與社群分析主控台")
print("="*50)

# 讓使用者選擇引擎
print("請選擇 AI 大腦引擎後端：")
print("1. OpenAI (雲端付費 - 需要 sk-... 金鑰)")
print("2. Ollama (本地開源 - 免費，需要電腦有運行 Ollama)")
print("3. 離線模擬 (完全免費 - 不需金鑰與 Ollama)")
choice_input = input("👉 請選擇 (1 - 3，預設為 3)：").strip()

if choice_input == "1":
    engine = "openai"
    mock_mode = False
    if not os.environ.get("OPENAI_API_KEY") or os.environ["OPENAI_API_KEY"] == "你的_sk-proj-開頭的Key":
        user_key = input("🔑 請輸入您的 OpenAI API Key：").strip()
        if user_key:
            os.environ["OPENAI_API_KEY"] = user_key
            api_key = user_key
        else:
            print("⚠️ 未提供金鑰，自動切換至離線模擬模式...")
            engine = "mock"
            mock_mode = True
            api_key = "MOCK_KEY"
    else:
        api_key = os.environ["OPENAI_API_KEY"]
elif choice_input == "2":
    engine = "ollama"
    mock_mode = False
    api_key = "OLLAMA_KEY"
    print("⚡ 已選擇 Ollama 本地開源引擎。請確保 `ollama serve` 已啟動...")
else:
    engine = "mock"
    mock_mode = True
    api_key = "MOCK_KEY"
    print("⚡ 已啟用離線模擬測試模式...")

# 2. 機器學習輿情擴散風險估算公式
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

# 讓使用者輸入自訂評論，或使用預設評論
default_review = "慕名去吃台南文章牛肉湯，結果排隊動線一團亂，店員態度還差到爆！最誇張的是，喝到一半發現湯裡竟然有一隻蒼蠅！跟店員反應還一副不耐煩的樣子，這種黑心排隊名店大家千萬別去，祝你們早點倒閉！"
print("\n請輸入您想測試的 Google 評論（直接按 Enter 將使用文章牛肉湯預設負評）：")
customer_review = input("👉 ").strip()
if not customer_review:
    customer_review = default_review

# 輸入星等
try:
    rating_input = input("⭐ 請給予星等 (1 - 5，預設為 1)：").strip()
    rating = int(rating_input) if rating_input else 1
    if not (1 <= rating <= 5):
        rating = 1
except ValueError:
    rating = 1

# 模擬圖片上傳
image_input = input("📸 是否模擬上傳佐證照片？(y / N，預設為 N)：").strip().lower()
has_image = image_input == 'y'

print("\n⚙️ 正在分析評論情緒...")

# 自動判定好評或負評
if mock_mode:
    positive_keywords = ["好吃", "推薦", "讚", "甜", "嫩", "大推", "服務好", "親切", "滿意", "好喝", "招牌"]
    is_positive = any(kw in customer_review for kw in positive_keywords)
    sentiment = "正面" if is_positive else "負面"
else:
    if engine == "openai":
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, openai_api_key=api_key)
    else:
        llm = ChatOllama(model="qwen2.5:3b", base_url="http://localhost:11434", temperature=0.7)
        
    classify_prompt = f"請判定以下顧客評論的客訴本質為正面（好評）還是負面（抱怨/客訴）？僅需輸出「正面」或「負面」二字，不要輸出其他字眼。\n\n評論：{customer_review}"
    response = llm.invoke(classify_prompt)
    sentiment = "正面" if "正面" in response.content else "負面"

print(f"🏷️ 系統自動判定評論屬性：\033[1;36m{sentiment}評論\033[0m")

# 3. 根據情緒與引擎載入對應的 RAG 庫
if sentiment == "負面":
    txt_file = "laws.txt"
    db_name = "法律資料庫 (laws.txt)"
else:
    txt_file = "menu.txt"
    db_name = "菜單資料庫 (menu.txt)"

if mock_mode:
    print(f"📚 直接自本地讀取並切片 {db_name} (離線模擬)...")
    with open(txt_file, "r", encoding="utf-8") as f:
        text_content = f.read()
    cheat_sheet = "\n".join([line.strip() for line in text_content.split("\n") if line.strip()][:2])
    print(f"🔍 正在進行語意相似度檢索...")
    print(f"✅ 已檢索到最相符的小抄條目。")
else:
    if engine == "ollama":
        # 本地 Ollama 模式：【關鍵提速優化】直接讀取整檔上下文，完全不呼叫向量模型
        print(f"📚 Ollama 極速版：直接讀取 {txt_file} 作為上下文，免除本地向量計算...")
        with open(txt_file, "r", encoding="utf-8") as f:
            cheat_sheet = f.read().strip()
        print(f"✅ 已載入小抄上下文。")
    else:
        # 真實 OpenAI 模式：使用 ChromaDB 進行語意相似度檢索
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small", openai_api_key=api_key)
        db_dir = f"./chroma_db_{txt_file.split('.')[0]}_openai"
        
        file_mtime = os.path.getmtime(txt_file) if os.path.exists(txt_file) else 0
        marker_file = os.path.join(db_dir, "mtime_marker.txt")
        saved_mtime = 0.0
        if os.path.exists(marker_file):
            try:
                with open(marker_file, "r") as mf:
                    saved_mtime = float(mf.read().strip())
            except:
                pass
                
        rebuild = not os.path.exists(db_dir) or len(os.listdir(db_dir)) == 0 or abs(file_mtime - saved_mtime) > 0.01
        
        if rebuild:
            print(f"📚 正在讀取並重新編譯 {db_name} ...")
            if os.path.exists(db_dir):
                shutil.rmtree(db_dir)
            os.makedirs(db_dir, exist_ok=True)
                
            with open(txt_file, "r", encoding="utf-8") as f:
                text_content = f.read()
            
            # 1. RAG 文件切片：針對結構化與條列式文件 (法規/菜單)，採用以行 (Line-based) 為基礎的切片方式，確保每一項內容語意完整
            chunks = [line.strip() for line in text_content.split("\n") if line.strip()]
            
            db_drawer = Chroma.from_texts(texts=chunks, embedding=embeddings, persist_directory=db_dir)
            with open(marker_file, "w") as mf:
                mf.write(str(file_mtime))
        else:
            print(f"📚 直接從磁碟載入已編譯的 {db_name} (省時且不消耗 API)...")
            db_drawer = Chroma(persist_directory=db_dir, embedding_function=embeddings)
            
        print("🔍 正在進行語意相似度檢索（含查詢重寫與歷史案例檢索）...")
        few_shot_examples = ""
        query_embedding = None
        try:
            llm_rewriter = ChatOpenAI(model="gpt-4o-mini", temperature=0, openai_api_key=api_key)
            rewrite_prompt = f"請根據以下顧客評論，提煉出最核心的 2-3 個檢索關鍵字或法律/菜單主旨（如：法規名稱、特定菜色、衛生問題），只輸出關鍵字，以空格分隔。不要輸出任何其他文字。\n\n評論：{customer_review}"
            rewritten_query = llm_rewriter.invoke(rewrite_prompt).content.strip()
            print(f"💡 提煉關鍵字為：{rewritten_query}")
            docs = db_drawer.similarity_search(rewritten_query, k=2)
            
            # 建立 OpenAIEmbeddings 產生查詢向量與 Supabase 檢索
            try:
                embeddings = OpenAIEmbeddings(model="text-embedding-3-small", openai_api_key=api_key)
                query_embedding = embeddings.embed_query(rewritten_query)
                from supabase_db import supabase, search_similar_reviews
                if supabase:
                    similar_cases = search_similar_reviews(query_embedding, rating=rating, limit=2)
                    if similar_cases:
                        print(f"✅ 成功自 Supabase 檢索到 {len(similar_cases)} 筆相似歷史案例。")
                        for i, case in enumerate(similar_cases):
                            few_shot_examples += f"【歷史案例 {i+1}】\n"
                            few_shot_examples += f"顧客評論：{case.get('review', '')}\n"
                            few_shot_examples += f"回覆報告：\n{case.get('report_content', '')}\n"
                            few_shot_examples += "----------------\n"
            except Exception as e_emb:
                print(f"[Warning] Failed to generate embedding or query Supabase: {e_emb}")
        except Exception:
            docs = db_drawer.similarity_search(customer_review, k=2)
        cheat_sheet = "\n".join([doc.page_content for doc in docs])
        print(f"✅ 已檢索到最相符的小抄條目。")

# 4. 計算輿情擴散風險
risk_percent = predict_diffusion_risk(sentiment, rating, has_image, customer_review)
print(f"\n📊 輿情擴散風險評估：\033[1;31m{risk_percent:.1f}%\033[0m")
if risk_percent >= 75.0:
    print("🚨 \033[1;31m警告：此評論擴散風險極高，屬於公關紅色警戒！\033[0m")
elif risk_percent >= 40.0:
    print("⚠️ \033[1;33m注意：此評論有一定擴散風險，請儘速處理。\033[0m")
else:
    print("ℹ️ \033[1;32m提示：此評論擴散風險較低。\033[0m")

# 5. 生成報告
print("\n✍️ 正在為老闆撰寫公關與行銷分析報告...")

if mock_mode:
    if sentiment == "負面":
        img_desc = "\n【🔍 照片視覺事證分析結果 (模擬)】：碗湯表面確實有一隻疑似蒼蠅的黑色小蟲。" if has_image else ""
        report_content = f"""{img_desc}

### 📊 1. 危機評估
* **危機等級**：🔴 高 / 黑色警戒
* **核心關鍵字**：食品衛生、餐點有蟲

### ⚖️ 2. 法務與內部應對策略
* **適用法規**：食品安全衛生管理法第 8 條。

### 📢 3. 公開回覆草稿 (Google 評論回覆)
> 敬愛的顧客您好，我是文章牛肉湯的負責人。非常抱歉讓您喝到異物。我們已要求清潔公司加強廚房消毒，並對當班員工進行教育訓練。請與我們私訊聯繫以利為您退款，再次抱歉。
"""
    else:
        report_content = """### 🌟 1. 滿意度分析
* **好評亮點**：溫體牛肉嫩、高湯鮮甜

### 📢 2. 公開致謝與推薦回覆
> 非常感謝您的熱情分享！下次推薦您也試試我們的牛肉燥飯和五花牛肉湯喔！
"""
else:
    # 真實 API 呼叫
    if not few_shot_examples:
        few_shot_examples = "（尚無歷史相似範本，請依公關專業直接撰寫）\n"

    if sentiment == "負面":
        system_template = """
        # 歷史優良回覆範例 (Few-shot Examples)
        {few_shot_examples}
        
        # 角色設定
        你現在是台南知名排隊名店【文章牛肉湯】的「資深公關危機暨法務策略總監」。
        請根據提供的【法律小抄】、【客訴評論】與【顧客佐證照片】（如有），寫出一份公關危機報告。
        若有照片，請新增「【🔍 照片視覺事證分析結果】」說明碗湯內是否有蟲。
        
        報告格式：
        ### 📊 1. 危機評估
        * **危機等級**：🔴 高 / 🟡 中 / 🟢 低
        ### ⚖️ 2. 法務與內部應對策略
        * **適用法規**：結合【法律小抄】。
        ### 📢 3. 公開回覆草稿
        ### ✉️ 4. 私訊安撫與補償模板

        [SCORE_START]
        SINCERITY: 90
        LEGAL_DEFENSE: 90
        REPUTATION_RECOVERY: 90
        [SCORE_END]
        ---
        【法律小抄】：{laws}
        """
    else:
        system_template = """
        # 歷史優良回覆範例 (Few-shot Examples)
        {few_shot_examples}
        
        # 角色設定
        你現在是【文章牛肉湯】的「首席社群品牌與行銷經理」。
        請根據提供的【菜單小抄】與【好評評論】，寫一封熱情誠摯的感謝信，並結合小抄推薦 1-2 道招牌菜。

        報告格式：
        ### 🌟 1. 滿意度分析
        ### 📢 2. 公開致謝與推薦回覆
        ### 🎁 3. 常客專屬小驚喜建議

        [SCORE_START]
        SINCERITY: 95
        LEGAL_DEFENSE: 60
        REPUTATION_RECOVERY: 95
        [SCORE_END]
        ---
        【菜單小抄】：{laws}
        """

    prompt_template = ChatPromptTemplate.from_messages([
        ("system", system_template),
        ("user", "{customer_review}")
    ])

    ai_chain = prompt_template | llm
    response = ai_chain.invoke({
        "customer_review": customer_review,
        "laws": cheat_sheet,
        "few_shot_examples": few_shot_examples
    })
    report_content = response.content
    
    # 移除分數區塊
    score_start_idx = report_content.find("[SCORE_START]")
    score_end_idx = report_content.find("[SCORE_END]")
    if score_start_idx != -1 and score_end_idx != -1:
        report_content = (report_content[:score_start_idx] + report_content[score_end_idx + len("[SCORE_END]"):].strip())

# 6. 顯示報告成果
print("\n" + "="*20 + " 最終生成的商家分析報告 " + "="*20)
print(report_content)
print("="*65)
if mock_mode:
    print("* (提示：此為離線模擬報告，無 API 消耗)")