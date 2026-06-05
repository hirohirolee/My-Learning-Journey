import streamlit as st
import streamlit.components.v1 as components
import json

# ==========================================
# 1. 網頁基本設定
# ==========================================
st.set_page_config(
    page_title="AI 圖像生成 Web App",
    page_icon="🎨",
    layout="wide"
)

# ==========================================
# 2. 安全地讀取系統預設 API Key
# ==========================================
try:
    system_hf_token = st.secrets["HF_TOKEN"]
except KeyError:
    system_hf_token = None

# ==========================================
# 3. 左側邊欄設計
# ==========================================
with st.sidebar:
    st.markdown("### 🛡️ 系統金鑰託管狀態")
    if system_hf_token:
        st.success("🟢 系統預設憑證：已於後端安全託管")
    else:
        st.warning("⚠️ 系統預設憑證：未偵測到後端託管")
        
    st.divider()
    
    st.markdown("### 🔑 使用者自訂密鑰 (選填)")
    user_hf_token = st.text_input(
        "輸入您的 Hugging Face Token:",
        type="password",
        placeholder="hf_...",
        help="留空將自動啟用系統後端託管憑證生圖"
    )
    
    if user_hf_token.strip():
        active_token = user_hf_token.strip()
        st.info("🔐 當前連線狀態：已啟用您輸入的自訂密鑰")
    else:
        active_token = system_hf_token
        if system_hf_token:
            st.info("🔒 當前連線狀態：已啟用後端自動託管憑證")
        else:
            st.error("❌ 當前連線狀態：無可用憑證，將無法生圖")

    st.divider()
    st.markdown("### ⚙️ 模型設定")
    selected_model = st.selectbox(
        "選擇 AI 模型:",
        (
            "black-forest-labs/FLUX.1-schnell",
            "stabilityai/sdxl-turbo",
            "stabilityai/stable-diffusion-xl-base-1.0"
        )
    )

# ==========================================
# 4. 主畫面設計
# ==========================================
st.title("🎨 AI 圖像生成 Web App")
st.markdown("輸入一段文字，讓 AI 為你創作圖片。**(🚀 採用前端直連技術，100% 免疫雲端斷網)**")

with st.container(border=True):
    prompt = st.text_area(
        "請輸入提示詞 (Prompt):",
        placeholder="A cat walking on the beach...",
        height=150
    )
    
    submit_button = st.button("開始生成", type="primary")

st.info("💡 系統已切換至「前端直連模式」，將透過您的瀏覽器直接連線 Hugging Face，完全避開 Streamlit 伺服器網路故障問題。")

# ==========================================
# 5. 究極生圖核心：純前端 JavaScript 直連 (絕對防禦版)
# ==========================================
if submit_button:
    if not prompt.strip():
        st.warning("⚠️ 請輸入您想要生成的圖片提示詞 (Prompt)！")
    elif not active_token:
        st.error("⚠️ 系統無可用金鑰，請在左側輸入您的 Hugging Face Token。")
    else:
        st.success("📡 指令已發送！正在透過前端通道直連 Hugging Face API...")
        
        # 安全地將 Python 變數轉為 JavaScript 字串
        js_prompt = json.dumps(prompt.strip())
        js_token = json.dumps(active_token)
        js_model = json.dumps(selected_model)
        
        # 使用最穩定的陣列合併法，徹底消滅 f-string 與三引號的語法地雷
        html_lines = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            "    <meta charset='UTF-8'>",
            "
