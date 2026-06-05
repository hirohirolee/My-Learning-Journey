import streamlit as st
import requests
import io
import time
import urllib.parse
from PIL import Image

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
st.markdown("**(✨ 具備 DNS 斷網容錯機制的終極版本)**")

prompt = st.text_area("請輸入提示詞 (Prompt):", placeholder="A cat walking on the beach...", height=150)
submit_button = st.button("開始生成", type="primary")

# ==========================================
# 5. 核心邏輯
# ==========================================
if submit_button:
    if not prompt.strip():
        st.warning("⚠️ 請輸入提示詞！")
    elif not active_token:
        st.error("⚠️ 無可用金鑰！")
    else:
        API_URL = f"https://api-inference.huggingface.co/models/{selected_model}"
        headers = {"Authorization": f"Bearer {active_token}"}
        payload = {"inputs": prompt.strip()}
        
        status_msg = st.empty()
        success = False
        
        # 嘗試連線 Hugging Face
        for attempt in range(3):
            status_msg.info(f"🚀 正在連線雲端模型... (第 {attempt + 1} 次嘗試)")
            try:
                response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
                
                if response.status_code == 200:
                    image = Image.open(io.BytesIO(response.content))
                    status_msg.success("🎉 圖片生成成功！")
                    st.image(image, caption=f"✨ {prompt.strip()} (Hugging Face)", use_container_width=True)
                    success = True
                    break
                elif response.status_code == 503:
                    wait_time = response.json().get("estimated_time", 15.0)
                    status_msg.warning(f"⏳ 模型喚醒中，系統將等待 {min(wait_time, 15):.1f} 秒...")
                    time.sleep(min(wait_time, 15))
                else:
                    status_msg.error(f"❌ API 錯誤: {response.status_code}")
                    break
                    
            except requests.exceptions.ConnectionError:
                # 抓到最致命的 DNS 斷網錯誤 (NameResolutionError)
                status_msg.error("🚨 致命錯誤：Streamlit 雲端伺服器對外網路已斷線！")
                break
            except Exception as e:
                status_msg.warning("⚠️ 連線異常，準備重試...")
                time.sleep(2)

        # 如果後端徹底死機或超時，啟用瀏覽器物理繞道
        if not success:
            st.warning("📡 後端網路故障，已啟動【前端瀏覽器直連模式】渲染圖片！")
            encoded_prompt = urllib.parse.quote(prompt.strip())
            fallback_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?nologo=true"
            
            # 使用純 HTML 讓你的「瀏覽器」去下載圖片，完全不管 Streamlit 伺服器死活
            html_img = f'<div style="display:flex;justify-content:center;"><img src="{fallback_url}" width="100%" style="border-radius:10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);"></div>'
            st.markdown(html_img, unsafe_allow_html=True)
            st.caption(f"✨ {prompt.strip()} (瀏覽器渲染備用通道)")
