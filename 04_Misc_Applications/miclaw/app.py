import streamlit as st
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
import os

# 網頁基本設定
st.set_page_config(page_title="BizAgent 商務出差特務", page_icon="💼", layout="centered")

st.title("💼 BizAgent 商務出差與行程管理特務")
st.markdown("本系統模擬一個自主 AI Agent，接收出差需求並在背景調用模擬工具，為您產出專業的出差準備計畫。(採用雲端免費 Groq 服務)")

# ==========================================
# 系統提示詞 (System Prompt) 定義區
# ==========================================
SYSTEM_PROMPT = """
# Role & Goal
你是一個名為「BizAgent」的跨國/國內商業出差與商務行程管理特務 Agent。
你的任務是接受使用者的出差需求（例如：前往特定城市開會、拜訪客戶、參加展覽），像一個真正的自主 AI Agent 一樣，將任務拆解為多個商務子任務，模擬呼叫適當的工具（Tools），最後彙整數據產出高品質、結構化且具備商業專業感的出差準備計畫。

---

# Available Internal Tools (模擬工具庫)
當你收到使用者出差指令時，你「必須」在思考過程中模擬呼叫以下工具來獲取數據（請勿空想數據，要在思考軌跡中顯示工具調用過程）：

1. `Business_Travel_Weather_API(location: str)`
   - 功能：獲取出差目的地的天氣、溫差、降雨機率，並給出適當的「商務正裝/休閒便服穿著建議」。
2. `Expense_and_Budget_Estimator(city: str, days: int, level: str)`
   - 功能：估算該城市的合理出差預算（含每日餐費上限 Per Diem、交通計程車費、住宿預估與雜費），方便後續報帳規劃。
3. `Business_Checklist_Generator(trip_type: str)`
   - 功能：針對特定商務出差類型（國內快閃拜訪、跨國開會、展覽參展）生成專業的文件、3C 設備與個人行李 Check-list。

---

# Execution Protocol (執行規範)

在回答任何出差需求時，你的輸出必須嚴格包含以下「兩個核心區塊」：

### 區塊一：🔄 Agentic Workflow Trace (思考與工具執行軌跡)
在此區塊，你需要展示你的「思考邏輯（CoT）」與「工具呼叫過程（Tool Calling Trace）」。
請使用以下格式呈現：
- 🧠 **[意圖解析]**：解析使用者出差地點、天數、目的與潛在商務需求。
- 🛠️ **[自主決策 1]**：說明需要調用哪個工具與傳入的參數 -> 顯示模擬回傳的 JSON 數據。
- 🛠️ **[自主決策 2]**：說明下一個調用的工具與參數 -> 顯示模擬回傳的 JSON 數據。
- 🛠️ **[自主決策 3]**：說明下一個調用的工具與參數 -> 顯示模擬回傳的 JSON 數據。
- 📝 **[綜合報告生成]**：說明如何將上述工具數據彙整為最終商務出差報告。

---

### 區塊二：📄 最終 Agent 產出的出差準備簡報
根據工具回傳的數據，為使用者生成一份格式專業、清晰且可直接列印/存檔的 Markdown 出差簡報，必須包含：
1. **🌤️ 目的地的天候與商務穿著指南**（結合 Weather 數據，包含氣溫與穿著搭配建議）
2. **💰 出差預算與報帳估算表**（結合 Expense 數據，提供餐費上限、交通與住宿參考，便於財務核銷）
3. **💼 出差必備清單 (Business Checklist)**（結合 Checklist 數據，包含重要文件、3C 名片/簡報設備、個人用品，使用 `- [ ]` 複選框格式）

---

# Tone & Style
- 語氣：高效率、嚴謹、專業的資深商務特務/幕僚語氣。
- 語言：繁體中文（Taiwan Traditional Chinese）。
- 當使用者輸入的需求缺少部分細節（例如沒說去幾天），請自動做合理的預設（例如預設 3 天 2 夜）並在思考軌跡中說明。
"""

# ==========================================
# UI 與狀態管理
# ==========================================
with st.sidebar:
    st.header("⚙️ 模型設定")
    groq_api_key = st.text_input("🔑 Groq API Key", type="password", help="請至 https://console.groq.com/keys 免費獲取")
    model_name = st.selectbox("模型名稱", ["llama3-70b-8192", "llama3-8b-8192", "mixtral-8x7b-32768"], index=0)
    temperature = st.slider("創意程度 (Temperature)", min_value=0.0, max_value=1.0, value=0.7, step=0.1)
    
    if st.button("🗑️ 清除對話紀錄", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# 初始化對話紀錄
if "messages" not in st.session_state:
    st.session_state.messages = []
    # 可以放一個初始歡迎訊息
    st.session_state.messages.append({"role": "assistant", "content": "您好，我是 BizAgent 您的專屬商務出差特務。請告訴我您即將出差的目的地與需求（例如：「下週要去東京參加 AI 科技展覽，大約三天」），我將立即為您模擬調用工具並產生完整的準備計畫。"})

# 顯示歷史對話
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ==========================================
# 接收使用者輸入與處理
# ==========================================
if prompt := st.chat_input("請輸入您的出差需求..."):
    # 1. 顯示使用者輸入
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. 呼叫 LLM 生成回應
    with st.chat_message("assistant"):
        if not groq_api_key:
            st.warning("⚠️ 請先在左側邊欄輸入您的 Groq API Key！")
            st.stop()
            
        with st.spinner("BizAgent 正在解析意圖，並模擬調用工具庫中..."):
            try:
                # 建立模型物件
                llm = ChatGroq(model=model_name, temperature=temperature, groq_api_key=groq_api_key)
                
                # 組合對話歷史 (包含 System Prompt)
                langchain_messages = [SystemMessage(content=SYSTEM_PROMPT)]
                for m in st.session_state.messages:
                    if m["role"] == "user":
                        # 強制在每次使用者對話後方加上提示，確保 LLM 記得用中文
                        langchain_messages.append(HumanMessage(content=m["content"] + "\n\n【重要指令：你接下來所有的思考軌跡與最終報告，都必須嚴格使用『繁體中文 (Taiwan Traditional Chinese)』輸出，絕對不可以使用英文！】"))
                    elif m["role"] == "assistant":
                        langchain_messages.append(AIMessage(content=m["content"]))
                
                # 取得回應
                response = llm.invoke(langchain_messages)
                
                # 顯示並儲存結果
                st.markdown(response.content)
                st.session_state.messages.append({"role": "assistant", "content": response.content})
                
            except Exception as e:
                st.error(f"⚠️ 發生錯誤：{e}")
                st.info("請確認：\n1. 您的 API Key 是否正確輸入。\n2. 網路連線是否正常。")
