import streamlit as st
import streamlit.components.v1 as components
import urllib.parse
import random

# ==========================================
# 1. 網頁基本設定
# ==========================================
st.set_page_config(
    page_title="AI 圖像生成 Web App",
    page_icon="🎨",
    layout="wide"
)

# ==========================================
# 2. 安全地讀取系統預設 API Key (後端自動託管)
# ==========================================
try:
    system_hf_token = st.secrets["HF_TOKEN"]
except KeyError:
    system_hf_token = None

# ==========================================
# 3. 左側邊欄設計 (自訂密鑰雙軌機制)
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
            st.error("❌ 當前連線狀態：無可用憑證，將使用備用免 Key 通道出圖")

    st.divider()
    st.markdown("### ⚙️ 模型設定")
    selected_model = st.selectbox(
        "選擇 AI 模型:",
        (
            "black-forest-labs/FLUX.1-schnell",
            "stabilityai/sdxl-turbo",
            "stabilityai/stable-diffusion-xl-base-1.0",
            "nvidia/Cosmos3-Super-Text2Image"
        )
    )

# ==========================================
# 4. 主畫面設計
# ==========================================
st.title("🎨 AI 圖像生成 Web App")
st.markdown("輸入一段文字，讓 AI 為你創作圖片。**(支援金鑰自訂，免填則自動啟用託管憑證)**")

with st.container(border=True):
    prompt = st.text_area(
        "請輸入提示詞 (Prompt):",
        placeholder="An astronaut riding a horse on mars, hd, dramatic lighting",
        height=150
    )
    
    submit_button = st.button("開始生成", type="primary")

st.info("註：若遠端 Hugging Face 機房流量爆滿或斷線，系統將無縫啟用【備用免 Key 閃電生圖通道】，確保 100% 成功出圖。")

# ==========================================
# 5. 雙軌生成核心邏輯 (Hugging Face 優先 ➔ 備用免 Key Turbo 閃電繪圖)
# ==========================================
if submit_button:
    if not prompt.strip():
        st.warning("⚠️ 請輸入您想要生成的圖片提示詞 (Prompt)！")
    else:
        trigger_fallback = False
        
        # 通道一：嘗試連線 Hugging Face 官方 API
        if active_token:
            with st.spinner(f"正在嘗試連線遠端伺服器使用 {selected_model} 生成圖片..."):
                try:
                    import requests
                    import io
                    from PIL import Image
                    
                    API_URL = f"https://api-inference.huggingface.co/models/{selected_model}"
                    headers = {"Authorization": f"Bearer {active_token}"}
                    payload = {"inputs": prompt.strip()}
                    
                    # 設定 6 秒超時，防止轉圈圈過久
                    response = requests.post(API_URL, headers=headers, json=payload, timeout=6)
                    
                    if response.status_code == 200:
                        image_bytes = response.content
                        image = Image.open(io.BytesIO(image_bytes))
                        st.success("🎉 [通道一] Hugging Face 圖片生成成功！")
                        st.image(image, caption=prompt.strip(), use_container_width=True)
                    else:
                        trigger_fallback = True
                except Exception:
                    # 抓到雲端網路斷線錯誤，自動標記進入備用通道
                    trigger_fallback = True
        else:
            trigger_fallback = True

        # 通道二：備用免 Key 閃電生圖通道 (100% 成功秒級出圖關鍵)
        if trigger_fallback:
            st.warning("📡 遠端主通道延遲/斷線，已自動為您切換至【備用免 Key 閃電生圖通道】！")
            
            # 安全網址編碼與隨機種子防快取塞車
            encoded_prompt = urllib.parse.quote(prompt.strip().replace('\n', ' '))
            random_seed = random.randint(1, 99999)
            
            # 換用真正的極速 turbo 通道，速度增快 10 倍！
            target_image_url = f"https://image.pollinations.ai/p/{encoded_prompt}?width=800&height=600&model=turbo&seed={random_seed}"
            
            # 採用三個單引號包裹高質感前端生圖 UI
            html_template = '''
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <script src="https://cdn.tailwindcss.com"></script>
                <style>
                    @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: .4; } }
                    .animate-pulse { animation: pulse 1.5s cubic-bezier(0.4, 0, 0.6, 1) infinite; }
                </style>
            </head>
            <body class="bg-white p-0 m-0 flex flex-col items-center justify-center">
                <div class="w-full border border-slate-200 rounded-xl overflow-hidden shadow-lg bg-slate-50 relative p-4">
                    
                    <div class="relative rounded-lg overflow-hidden bg-slate-200 min-h-[450px] flex items-center justify-center">
                        
                        <div id="skeleton" class="absolute inset-0 flex flex-col items-center justify-center bg-slate-100 text
