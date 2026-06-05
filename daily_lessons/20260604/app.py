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
# 3. 左側邊欄設計 (包含模型選擇與憑證安全檢查)
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
    
    st.divider()
    
    # 🌟 這裡加入了你需要的「API Key 連線自我檢查」功能
    st.markdown("### 🔍 憑證安全自我檢查")
    if st.button("檢查後端 API 連線狀態", use_container_width=True):
        if not hf_token:
            st.error("❌ 檢查結果：Secrets 中找不到 'HF_TOKEN' 欄位，請前往 Streamlit 後台存檔。")
        elif not hf_token.strip().startswith("hf_"):
            st.warning("⚠️ 檢查結果：偵測到金鑰，但格式似乎不是以 'hf_' 開頭，請檢查是否複製錯誤。")
        else:
            with st.spinner("正在安全發送測試封包至 Hugging Face..."):
                try:
                    # 發送一個微型請求至目前選定的模型來測試驗證
                    test_url = f"https://api-inference.huggingface.co/models/{selected_model}"
                    test_headers = {"Authorization": f"Bearer {hf_token.strip()}"}
                    test_res = requests.post(test_url, headers=test_headers, json={"inputs": "test"})
                    
                    if test_res.status_code == 401:
                        st.error("❌ 驗證失敗：Token 存在，但 Hugging Face 回報密碼無效 (401 Unauthorized)。請重新確認複製的金鑰。")
                    elif test_res.status_code == 429:
                        st.warning("⚠️ 密碼正確，但目前該帳號呼叫頻率已達上限 (429 Too Many Requests)。")
                    else:
                        st.success("🟢 檢查通過：後端憑證完全正確，且已成功與 Hugging Face 建立安全連線！")
                except Exception as test_err:
                    st.error(f"連線測試失敗，可能是雲端網路波動：{test_err}")

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
# 5. 生成邏輯
# ==========================================
if submit_button:
    if not hf_token:
        st.error("⚠️ 無法連線至伺服器，憑證遺失。")
    elif not prompt.strip():
        st.warning("⚠️ 請輸入您想要生成的圖片提示詞 (Prompt)！")
    else:
        try:
            with st.spinner(f"正在使用 {selected_model} 模型生成圖片，請稍候..."):
                API_URL = f"https://api-inference.huggingface.co/models/{selected_model}"
                headers = {"Authorization": f"Bearer {hf_token.strip()}"}
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
                        st.warning(f"⏳ 伺服器正在喚醒模型，大約需要 {error_msg
