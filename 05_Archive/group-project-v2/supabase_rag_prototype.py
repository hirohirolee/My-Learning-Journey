import os
import sys
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# 確保能導入專案內的其他模組
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from supabase_db import supabase, SUPABASE_TABLE_NAME
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate

def search_similar_reviews_supabase(query_vector, rating, match_threshold=0.6, limit=2):
    """
    呼叫 Supabase SQL RPC (match_reviews) 進行向量語意相似度檢索，並限定相同評分 (rating) 的歷史案例
    """
    if not supabase:
        print("⚠️ Supabase 用戶端未初始化，無法進行檢索！")
        return []
    
    try:
        # 呼叫 Supabase 的 RPC 預存程序
        response = supabase.rpc(
            "match_reviews",
            {
                "query_embedding": query_vector,
                "match_threshold": match_threshold,
                "match_count": limit,
                "filter_rating": int(rating)
            }
        ).execute()
        return response.data
    except Exception as e:
        print(f"❌ Supabase RPC 檢索失敗：{str(e)}")
        print("💡 請確認已在 Supabase 執行 SQL 腳本建立 match_reviews 函數。")
        return []

def run_supabase_rag_flow(customer_review: str, rating: int, api_key: str):
    """
    執行完整的 Supabase RAG 與 Few-shot 報告生成流程
    """
    print("\n" + "="*50)
    print("🚀 啟動 Supabase pgvector RAG + Few-Shot 生成原型測試")
    print("="*50)
    
    # 1. 產生新評論的 Embedding 向量 (使用 OpenAI)
    print("🔮 1. 正在將新評論轉化為向量...")
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small", openai_api_key=api_key)
    query_vector = embeddings.embed_query(customer_review)
    
    # 2. 從 Supabase 檢索歷史相似的客訴回覆範本 (元數據過濾：相同 rating)
    print(f"🔍 2. 正在從 Supabase 檢索星等為 {rating} 星的相似歷史案例...")
    similar_cases = search_similar_reviews_supabase(query_vector, rating=rating, limit=2)
    
    # 3. 組合 Few-shot (少樣本) 上下文
    print("📝 3. 正在組合 Few-shot 上下文與 Prompt...")
    few_shot_context = ""
    if similar_cases:
        print(f"✅ 成功找到 {len(similar_cases)} 筆相似歷史案例！")
        for i, case in enumerate(similar_cases):
            few_shot_context += f"【歷史相似案例 {i+1}】\n"
            few_shot_context += f"顧客評論：{case.get('review', '')}\n"
            few_shot_context += f"審核通過的公關報告：\n{case.get('report_content', '')}\n"
            few_shot_context += "-"*30 + "\n"
    else:
        print("ℹ️ 未找到相似星等的歷史案例，將以預設專業公關語氣生成。")
        few_shot_context = "（尚無歷史相似範本，請依公關專業直接撰寫）\n"
        
    # 4. 準備法律小抄（此處模擬 RAG 法律條文）
    laws_context = """
    食品安全衛生管理法第 8 條（食品良好衛生規範準則，不潔導致損害，業者應負賠償責任。）
    民法第 184 條侵權行為（故意或過失侵害他人權利者，負損害賠償責任。）
    """
    
    # 5. 設計 Few-shot Prompt
    system_prompt = """你現在是台南知名排隊名店【文章牛肉湯】的「資深公關危機暨法務策略總監」。

# 歷史優良回覆範例 (Few-shot Examples)
以下是過去針對相似星等客訴，經品牌總監審核通過的優質公關報告範本，請參考其回覆邏輯、語氣與補償額度：
{few_shot_examples}

---
# 法律依據小抄
{laws}

# 任務指示
請針對以下最新的顧客評論，撰寫一份條理清晰且可直接執行的「商家公關危機應對報告」。
顧客評論：{customer_review}
給予星等：{rating} 星

報告格式要求（Markdown）：
### 📊 1. 危機評估
* 危機等級：[🔴 高 / 🟡 中 / 🟢 低]
### ⚖️ 2. 法務與內部應對策略
* 適用法規：結合【法律依據小抄】。
### 📢 3. 公開回覆草稿（用於 Google 評論回覆）
> **【回覆主旨】**：文章牛肉湯對您的真誠致歉
> **【回覆內文】**：誠摯 of 公開道歉信。
"""
    
    prompt_template = ChatPromptTemplate.from_template(system_prompt)
    formatted_prompt = prompt_template.format(
        few_shot_examples=few_shot_context,
        laws=laws_context,
        customer_review=customer_review,
        rating=rating
    )
    
    # 6. 呼叫 LLM 生成報告
    print("🧠 4. 正在傳送給 LLM 進行 Few-shot 推理生成...")
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2, openai_api_key=api_key)
    response = llm.invoke(formatted_prompt)
    
    print("\n" + "="*50)
    print("✨ 生成的危機公關報告結果：")
    print("="*50)
    print(response.content)
    print("="*50)

if __name__ == "__main__":
    # 快速本地測試範例
    test_review = "喝牛肉湯發現裡面有一隻蒼蠅！太噁心了吧，店員還很不耐煩！"
    test_rating = 1
    
    # 取得測試 API Key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("⚠️ 未偵測到 OPENAI_API_KEY 環境變數，請在環境變數或 .env 中設定後再行測試。")
    else:
        run_supabase_rag_flow(test_review, test_rating, api_key)
