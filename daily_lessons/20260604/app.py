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
# 2. 安全地讀取 API Key
# ==========================================
try:
    hf_token = st.secrets["HF_TOKEN"]
except KeyError:
    st.error("系統錯誤：找不到後端憑證，請在本地設定 .streamlit/secrets.toml。")
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
st.markdown("輸入一段文字，讓 AI 為你創作圖片。")

with st.container(border=True):
    prompt = st.text_area(
        "請輸入提示詞 (Prompt):",
        placeholder="An astronaut riding a horse on mars...",
        height=150
    )
    submit_button = st.button("開始生成", type="primary")

# ==========================================
# 5. 生成邏輯
# ==========================================
if submit_button:
    if not hf_token:
        st.error("⚠️ 憑證遺失，請檢查 secrets 設定。")
    elif not prompt.strip():
        st.warning("⚠️ 請輸入提示詞！")
    else:
        with st.spinner(f"正在使用 {selected_model} 模型生成圖片..."):
            try:
                API_URL = f"https://api-inference.huggingface.co/models/{selected_model}"
                headers = {"Authorization": f"Bearer {hf_token.strip()}"}
                payload = {"inputs": prompt.strip()}
                
                response = requests.post(API_URL, headers=headers, json=payload, timeout=20)
                
                if response.status_code == 200:
                    image_bytes = response.content
                    image = Image.open(io.BytesIO(image_bytes))
                    st.success("🎉 圖片生成成功！")
                    st.image(image, caption=prompt.strip(), use_container_width=True)
                else:
                    st.error(f"❌ 生成失敗 (狀態碼: {response.status_code})")
                    st.write(response.json())
            except Exception as e:
                st.error(f"發生連線錯誤：{e}")
