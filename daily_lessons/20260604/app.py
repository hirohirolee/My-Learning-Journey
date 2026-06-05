import streamlit as st
import requests
import io
from PIL import Image

# ==========================================
# 1. 網頁基本設定
# ==========================================
st.set_page_config(
    page_title="AI 圖像生成 Web App",
    page_icon="🎨",
    layout="wide"
)

# ==========================================
# 2. 安全地讀取 API Key (終端使用者完全不可見)
# ==========================================
try:
    hf_token = st.secrets["HF_TOKEN"]
except KeyError:
    st.error("系統錯誤：找不到後端憑證，請開發者確認 Secrets 設定。")
    hf_token = None

# ==========================================
# 3. 左側邊欄設計
# ==========================================
with st.sidebar:
    st.markdown("### 🛡️ 系統狀態")
    st.success("API 憑證已由後端安全接管")
    
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
st.markdown("輸入一段文字，讓 AI 為你創作圖片。**(完全免費，免填金鑰)**")

with st.container(border=True):
    prompt = st.text_area(
        "請輸入提示詞 (Prompt):",
        placeholder="An astronaut riding a horse on mars, hd, dramatic lighting",
        height=150
    )
    
    submit_button = st.button("開始生成", type="primary")

st.info("註：若生成失敗，可能是 Hugging Face 免費伺服器正在載入模型，請稍等一分鐘後再試。")

# ==========================================
# 5. 生成邏輯 (優化架構版)
# ==========================================
if submit_button:
    if not hf_token:
        st.error("⚠️ 無法連線至伺服器，憑證遺失。")
    elif not prompt.strip():
        st.warning("⚠️ 請輸入您想要生成的圖片提示詞 (Prompt)！")
    else:
        # 將 try 區塊往外提，保護整個運算與渲染過程
        try:
            with st.spinner(f"正在使用 {selected_model} 模型生成圖片，請稍候..."):
                API_URL = f"https://api-inference.huggingface.co/models/{selected_model}"
                headers = {"Authorization": f"Bearer {hf_token}"}
                payload = {"inputs": prompt.strip()}
                
                response = requests.post(API_URL, headers=headers, json=payload)
                
                if response.status_code == 200:
                    image_bytes = response.content
                    image = Image.open(io.BytesIO(image_bytes))
                    st.success("🎉 圖片生成成功！")
                    st.image(image, caption=prompt.strip(), use_container_width=True)
                else:
                    error_msg = response.json()
                    st.error(f"❌ 生成失敗 (狀態碼: {response.status_code})")
                    if isinstance(error_msg, dict) and "estimated_time" in error_msg:
                        st.warning(f"⏳ 伺服器正在喚醒模型，大約需要 {error_msg['estimated_time']:.1f} 秒，請稍後再點擊一次生成。")
                    else:
                        st.write(error_msg)
                        
        except Exception as e:
            # 完美的例外攔截
            if "NameResolutionError" in str(e) or "HTTPSConnection" in str(e) or "connection" in str(e).lower():
                st.error("❌ 網路連線異常：目前 Streamlit 雲端伺服器與 Hugging Face 連線中斷，請稍等幾秒鐘並重新整理網頁再試一次！")
            else:
                st.error(f"發生未知錯誤：{e}")
