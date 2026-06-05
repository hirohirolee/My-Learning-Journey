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
        st.success("🟢 系統預設憑證：已安全託管")
    else:
        st.warning("⚠️ 系統預設憑證：未設定")
        
    st.divider()
    user_hf_token = st.text_input("🔑 使用者自訂密鑰 (選填):", type="password", placeholder="hf_...")
    active_token = user_hf_token.strip() if user_hf_token.strip() else system_hf_token
    
    if active_token:
        st.info("🔐 憑證已就緒，準備連線")
    else:
        st.error("❌ 無可用憑證")

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

with st.container(border=True):
    prompt = st.text_area("請輸入提示詞 (Prompt):", placeholder="A cat walking on the beach...", height=150)
    submit_button = st.button("開始生成", type="primary")

# ==========================================
# 5. Hugging Face 智能喚醒重試核心
# ==========================================
if submit_button:
    if not prompt.strip():
        st.warning("⚠️ 請輸入提示詞！")
    elif not active_token:
        st.error("⚠️ 請提供有效金鑰！")
    else:
        API_URL = f"https://api-inference.huggingface.co/models/{selected_model}"
        headers = {"Authorization": f"Bearer {active_token}"}
        payload = {"inputs": prompt.strip()}
        
        # 建立動態訊息區
        status_msg = st.empty()
        success = False
        
        # 進行 3 次智能連線與喚醒嘗試
        for attempt in range(3):
            status_msg.info(f"🚀 正在連線 Hugging Face 算力池... (嘗試 {attempt + 1}/3)")
            try:
                response = requests.post(API_URL, headers=headers, json=payload, timeout=40)
                
                if response.status_code == 200:
                    image = Image.open(io.BytesIO(response.content))
                    status_msg.success("🎉 圖片生成成功！")
                    st.image(image, caption=f"✨ {prompt.strip()}", use_container_width=True)
                    success = True
                    break
                elif response.status_code == 503:
                    # 503 代表遠端免費模型剛睡醒，正在載入
                    wait_time = response.json().get("estimated_time", 15.0)
                    status_msg.warning(f"⏳ 遠端 AI 模型正在從休眠中喚醒... 系統自動等待 {min(wait_time, 15):.1f} 秒後重試...")
                    time.sleep(min(wait_time, 15))
                else:
                    status_msg.error(f"❌ API 回傳錯誤碼 {response.status_code}：{response.text}")
                    break
            except requests.exceptions.ConnectionError:
                status_msg.error("🚨 雲端機房目前仍處於斷網狀態 (NameResolutionError)，請執行左下角 Reboot 重新分配伺服器。")
                break
            except Exception as e:
                status_msg.warning(f"⚠️ 連線異常 ({str(e)})，準備重試...")
                time.sleep(2)
                
        if not success and 'response' in locals() and response.status_code == 503:
            st.error("❌ 遠端模型喚醒超時，請再點擊一次按鈕重新發送指令。")
