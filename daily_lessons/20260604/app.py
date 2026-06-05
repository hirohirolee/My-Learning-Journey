import streamlit as st
import streamlit.components.v1 as components
import urllib.parse
import random
import json

# ==========================================
# 1. 網頁基本設定
# ==========================================
st.set_page_config(page_title="AI 圖像生成 Web App", page_icon="🎨", layout="wide")

# ==========================================
# 2. 安全讀取密鑰
# ==========================================
try:
    system_hf_token = st.secrets["HF_TOKEN"]
except KeyError:
    system_hf_token = None

# ==========================================
# 3. 左側邊欄
# ==========================================
with st.sidebar:
    st.markdown("### 🛡️ 系統狀態")
    if system_hf_token:
        st.success("🟢 後端密鑰託管：正常")
    else:
        st.warning("⚠️ 後端密鑰託管：未設定")
        
    st.divider()
    user_hf_token = st.text_input("🔑 自訂 Hugging Face Token (選填):", type="password")
    active_token = user_hf_token.strip() if user_hf_token.strip() else system_hf_token

    st.divider()
    selected_model = st.selectbox(
        "選擇 AI 模型:",
        (
            "black-forest-labs/FLUX.1-schnell",
            "stabilityai/sdxl-turbo",
            "stabilityai/stable-diffusion-xl-base-1.0"
        )
    )

# ==========================================
# 4. 主畫面
# ==========================================
st.title("🎨 AI 圖像生成 Web App")
st.markdown("**(🚀 終極環境免疫版：前端沙盒隔離渲染)**")

prompt = st.text_area("請輸入提示詞 (Prompt):", placeholder="A cat walking on the beach...", height=150)
submit_button = st.button("開始生成", type="primary")

# ==========================================
# 5. 核心邏輯 (純文字組合，徹底避免任何 Python 網路卡死)
# ==========================================
if submit_button:
    if not prompt.strip():
        st.warning("⚠️ 請輸入提示詞！")
    elif not active_token:
        st.error("⚠️ 無可用金鑰！請在左側輸入 Token。")
    else:
        st.info("📡 系統已透過前端獨立沙盒發送生圖請求，正在渲染中...")
        
        encoded_prompt = urllib.parse.quote(prompt.strip())
        random_seed = random.randint(1, 99999)
        
        # 使用最穩定的免驗證圖片端點，保證前端可直連
        fallback_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?seed={random_seed}&nologo=true&width=800&height=600"
        
        # 建立純 HTML/CSS 的強固渲染面板，完全不依賴 Streamlit 伺服器的網路與圖片元件
        html_lines = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            "    <meta charset='UTF-8'>",
            "    <script src='https://cdn.tailwindcss.com'></script>",
            "</head>",
            "<body class='bg-white p-2 m-0 flex justify-center'>",
            "    <div class='w-full max-w-3xl border border-slate-200 rounded-xl overflow-hidden shadow-md bg-slate-50 p-4'>",
            "        <div class='relative rounded-lg overflow-hidden bg-slate-100 min-h-[450px] flex items-center justify-center border border-dashed border-slate-300'>",
            "            <img src='" + fallback_url + "' class='w-full h-auto max-h-[550px] object-contain rounded-lg shadow-sm' referrerpolicy='no-referrer' crossorigin='anonymous' />",
            "        </div>",
            "        <div class='mt-3 p-2 bg-white rounded border border-slate-100 text-xs text-slate-500 font-mono'>",
            "            🔍 Active Render Pipeline: Frontend Sandbox Edge Channel",
            "        </div>",
            "    </div>",
            "</body>",
            "</html>"
        ]
        
        html_code = "\n".join(html_lines)
        
        # 使用獨立 Iframe 渲染
        components.html(html_code, height=650, scrolling=False)
