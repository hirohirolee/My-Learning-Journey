import streamlit as st
import urllib.parse
import random
import requests
import io
from PIL import Image

# ==========================================
# 1. 網頁基本設定
# ==========================================
st.set_page_config(page_title="AI 圖像生成 Web App", page_icon="🎨", layout="wide")

# ==========================================
# 2. 安全地讀取系統預設 API Key
# ==========================================
try:
    system_hf_token = st.secrets["HF_TOKEN"]
except KeyError:
    system_hf_token = None

# ==========================================
# 3. 左側邊欄設計 (優雅專業 UI)
# ==========================================
with st.sidebar:
    st.markdown("### 🛡️ 系統金鑰託管狀態")
    if system_hf_token:
        st.success("🟢 系統預設憑證：已於後端安全託管")
    else:
        st.warning("⚠️ 系統預設憑證：未偵測到後端託管")
        
    st.divider()
    
    user_hf_token = st.text_input(
        "🔑 使用者自訂密鑰 (選填):",
        type="password",
        placeholder="hf_...",
        help="留空將自動啟用系統後端託管憑證"
    )
    
    if user_hf_token.strip():
        active_token = user_hf_token.strip()
        st.info("🔐 當前連線狀態：已啟用您輸入的自訂密鑰")
    else:
        active_token = system_hf_token
        if system_hf_token:
            st.info("🔒 當前連線狀態：已啟用後端自動託管憑證")
        else:
            st.error("❌ 當前連線狀態：無可用憑證，將使用備用通道")

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
# 4. 主畫面設計
# ==========================================
st.title("🎨 AI 圖像生成 Web App")
st.markdown("輸入一段文字，讓 AI 為你創作圖片。")

# 使用最簡單的輸入與按鈕，徹底避開元件衝突
prompt = st.text_area("請輸入提示詞 (Prompt):", placeholder="A cat walking on the beach...", height=150)
submit_button = st.button("開始生成", type="primary")

# ==========================================
# 5. 雙軌生圖邏輯 (Hugging Face -> Pollinations 備用直下載版)
# ==========================================
if submit_button:
    if not prompt.strip():
        st.warning("⚠️ 請輸入您想要生成的圖片提示詞 (Prompt)！")
    else:
        success_hf = False
        
        # 嘗試一：Hugging Face 官方 API
        if active_token:
            with st.spinner(f"正在連線 Hugging Face ({selected_model}) ..."):
                try:
                    API_URL = f"https://api-inference.huggingface.co/models/{selected_model}"
                    headers = {"Authorization": f"Bearer {active_token}"}
                    payload = {"inputs": prompt.strip()}
                    
                    # 設定 10 秒超時，超時或出錯就無痛切換
                    response = requests.post(API_URL, headers=headers, json=payload, timeout=10)
                    
                    if response.status_code == 200:
                        image_bytes = response.content
                        image = Image.open(io.BytesIO(image_bytes))
                        st.success("🎉 [主通道成功] Hugging Face 官方 API 圖片生成成功！")
                        st.image(image, caption=f"✨ {prompt.strip()} (Hugging Face)", use_container_width=True)
                        success_hf = True
                    else:
                        st.toast(f"Hugging Face 忙碌中 (狀態碼: {response.status_code})")
                except Exception as e:
                    st.toast("Hugging Face 雲端連線超時，啟動備用方案...")

        # 嘗試二：如果 HF 失敗，啟用備用免 Key 極速通道 (後端物理隔離下載版)
        if not success_hf:
            st.warning("📡 遠端主通道不穩，已自動為您切換至【備用極速通道】！")
            with st.spinner("🚀 備用 AI 矩陣渲染中..."):
                try:
                    # 先進行提示詞編碼與種子產生
                    encoded_prompt = urllib.parse.quote(prompt.strip())
                    random_seed = random.randint(1, 99999)
                    
                    # 備用網址：指定 Turbo 模型並強制尺寸，確保 1~3 秒內出圖
                    fallback_url = f"https://image.pollinations.ai/p/{encoded_prompt}?width=1024&height=768&model=turbo&seed={random_seed}"
                    
                    # 🌟 核心修正：我們不在瀏覽器解析網址，我們在 Python 後端直接下載真實圖片！
                    # 這將彻底免疫 Streamlit 元件卡死的問題
                    response_fallback = requests.get(fallback_url, timeout=15)
                    
                    if response_fallback.status_code == 200:
                        # 成功下載二進位數據，直接塞給 st.image
                        st.success("🎉 [備用通道成功] 備用 AI 圖片生成成功！")
                        st.image(response_fallback.content, caption=f"✨ {prompt.strip()} (Turbo 備用通道)", use_container_width=True)
                    else:
                        st.error(f"❌ 備用通道也發生錯誤，請稍後再試。 (狀態碼: {response_fallback.status_code})")
                        
                except Exception as e_fallback:
                    st.error(f"❌ 備用通道發生嚴重錯誤: {e_fallback}")
