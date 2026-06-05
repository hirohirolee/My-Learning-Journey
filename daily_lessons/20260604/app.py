import streamlit as st
import requests
import io
import time
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
# 3. 左側邊欄設計
# ==========================================
with st.sidebar:
    st.markdown("### 🛡️ 系統金鑰託管狀態")
    if system_hf_token:
        st.success("🟢 系統預設憑證：已安全託管")
    else:
        st.warning("⚠️ 系統預設憑證：未設定")
        
    st.divider()
    
    user_hf_token = st.text_input(
        "🔑 使用者自訂密鑰 (選填):",
        type="password",
        placeholder="hf_...",
        help="留空將自動啟用系統後端託管憑證"
    )
    
    # 決定最終使用的 Token
    active_token = user_hf_token.strip() if user_hf_token.strip() else system_hf_token
    
    if active_token == user_hf_token.strip() and active_token:
        st.info("🔐 已啟用您輸入的自訂密鑰")
    elif active_token == system_hf_token and active_token:
        st.info("🔒 已啟用後端自動託管憑證")
    else:
        st.error("❌ 無可用憑證，將無法生圖")

    st.divider()
    selected_model = st.selectbox(
        "選擇 AI 模型:",
        (
            "black-forest-labs/FLUX.1-schnell",
            "stabilityai/sdxl-turbo",
            "stabilityai/stable-diffusion-xl-base-1.0",
            "prompthero/openjourney"  # 加入一個較快喚醒的經典模型備用
        )
    )

# ==========================================
# 4. 主畫面設計
# ==========================================
st.title("🎨 AI 圖像生成 Web App")
st.markdown("**(✨ 最終穩定版：內建 Hugging Face 智能喚醒與重試引擎)**")

with st.container(border=True):
    prompt = st.text_area("請輸入提示詞 (Prompt):", placeholder="A cat walking on the beach...", height=150)
    submit_button = st.button("開始生成", type="primary")

# ==========================================
# 5. Hugging Face 專屬智能連線邏輯
# ==========================================
if submit_button:
    if not prompt.strip():
        st.warning("⚠️ 請輸入提示詞！")
    elif not active_token:
        st.error("⚠️ 系統無可用金鑰，請在左側輸入 Hugging Face Token！")
    else:
        API_URL = f"https://api-inference.huggingface.co/models/{selected_model}"
        headers = {"Authorization": f"Bearer {active_token}"}
        payload = {"inputs": prompt.strip()}
        
        max_retries = 6
        success = False
        
        # 建立一個動態更新狀態的區塊
        status_msg = st.empty()
        
        for attempt in range(max_retries):
            status_msg.info(f"🚀 正在連線 Hugging Face... (第 {attempt + 1}/{max_retries} 次嘗試)")
            
            try:
                # 放寬超時限制至 40 秒
                response = requests.post(API_URL, headers=headers, json=payload, timeout=40)
                
                if response.status_code == 200:
                    image = Image.open(io.BytesIO(response.content))
                    status_msg.success("🎉 圖片生成成功！")
                    st.image(image, caption=f"✨ {prompt.strip()}", use_container_width=True)
                    success = True
                    break
                    
                elif response.status_code == 503:
                    # 503 代表模型在休眠，讀取需要等待的時間
                    data = response.json()
                    wait_time = data.get("estimated_time", 20.0)
                    sleep_time = min(wait_time, 15)  # 每次最多等 15 秒避免網頁完全卡死
                    
                    status_msg.warning(f"⏳ 遠端模型正在從休眠中喚醒... 系統將在 {sleep_time} 秒後自動重試。")
                    time.sleep(sleep_time)
                    
                else:
                    status_msg.error(f"❌ API 發生錯誤 (狀態碼: {response.status_code}): {response.text}")
                    break
                    
            except requests.exceptions.Timeout:
                status_msg.warning("⚠️ 連線超時，正在準備重試...")
                time.sleep(3)
            except Exception as e:
                status_msg.error(f"❌ 發生異常錯誤: {str(e)}")
                break
                
        # 如果重試完畢依然失敗
        if not success and 'response' in locals() and response.status_code == 503:
            st.error("❌ 模型喚醒時間過長，已達到最大重試次數。建議稍後再試，或在左側更換其他模型。")
