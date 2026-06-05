import streamlit as st
import requests
import io
from PIL import Image

# ==========================================
# 1. 網頁基本設定 (Page Config)
# ==========================================
st.set_page_config(
    page_title="AI 圖像生成 Web App",
    page_icon="🎨",
    layout="wide" # 使用寬螢幕佈局
)

# ==========================================
# 2. 左側邊欄設計 (Sidebar)
# ==========================================
with st.sidebar:
    st.markdown("### 🔑 安全設定")
    # 使用 type="password" 讓輸入的 Token 變成隱碼
    hf_token = st.text_input("輸入 Hugging Face Token:", type="password", help="請輸入您的 Hugging Face Access Token")
    
    # 藍色提示框
    st.info("提示：此 Token 僅用於此次請求，不會被儲存。")
    
    st.divider() # 分隔線
    
    st.markdown("### ⚙️ 模型設定")
    # 下拉式選單選擇模型
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
# 3. 主畫面設計 (Main Content)
# ==========================================
st.title("🎨 AI 圖像生成 Web App")
st.markdown("輸入一段文字，讓 AI 為你創作圖片。")

# 使用 container 建立一個帶有邊框的輸入區塊 (Streamlit 1.30+ 支援 border=True)
with st.container(border=True):
    prompt = st.text_area(
        "請輸入提示詞 (Prompt):",
        placeholder="An astronaut riding a horse on mars, hd, dramatic lighting",
        height=150
    )
    
    # 生成按鈕
    submit_button = st.button("開始生成")

# 藍色提示說明
st.info("註：若生成失敗，可能是 Hugging Face 免費伺服器正在載入模型，請稍等一分鐘後再試。")

# ==========================================
# 4. 生成邏輯 (Backend Logic)
# ==========================================
if submit_button:
    # 防呆機制：檢查是否輸入了 Token 與提示詞
    if not hf_token:
        st.error("⚠️ 請先在左側邊欄輸入您的 Hugging Face Token！")
    elif not prompt.strip():
        st.warning("⚠️ 請輸入您想要生成的圖片提示詞 (Prompt)！")
    else:
        # 顯示載入動畫
        with st.spinner(f"正在使用 {selected_model} 模型生成圖片，請稍候..."):
            try:
                # 設定 API 網址與標頭
                API_URL = f"https://api-inference.huggingface.co/models/{selected_model}"
                headers = {"Authorization": f"Bearer {hf_token}"}
                payload = {"inputs": prompt.strip()}
                
                # 發送請求至 Hugging Face
                response = requests.post(API_URL, headers=headers, json=payload)
                
                # 判斷是否成功
                if response.status_code == 200:
                    image_bytes = response.content
                    image = Image.open(io.BytesIO(image_bytes))
                    st.success("🎉 圖片生成成功！")
                    st.image(image, caption=prompt, use_container_width=True)
                else:
                    # 處理伺服器正在載入模型 (Model loading) 或其他錯誤
                    error_msg = response.json()
                    st.error(f"❌ 生成失敗 (狀態碼: {response.status_code})")
                    if "estimated_time" in error_msg:
                        st.warning(f"⏳ 伺服器正在喚醒模型，大約需要 {error_msg['estimated_time']:.1f} 秒，請稍後再點擊一次生成。")
                    else:
                        st.write(error_msg)
            
            except Exception as e:
                st.error(f"發生未知錯誤：{e}")
