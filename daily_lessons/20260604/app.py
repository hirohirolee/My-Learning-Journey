import streamlit as st
import requests

# 設定網頁標題與寬度
st.set_page_config(page_title="AI 圖像生成 Web App", page_icon="🎨", layout="centered")

# ==========================================
# 🔑 關鍵設定區：請務必填入您的專屬 Token
# ==========================================
# 請將下方的字串替換成您在 Hugging Face 申請的 Token (必須保留雙引號)
HF_TOKEN = "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"

# 使用官方推薦、畫質極佳的 SDXL 模型
API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
headers = {"Authorization": f"Bearer {HF_TOKEN}"}

st.title("🎨 AI 圖像生成 Web App")
st.markdown("本系統已直連 Hugging Face 官方伺服器，提供穩定高畫質的 AI 圖像生成服務。")

# 提示詞輸入框
prompt = st.text_area("請輸入提示詞 (Prompt):", "a cat walking on the beach")

# 生成按鈕
if st.button("開始生成", type="primary"):
    # 檢查是否忘記填 Token
    if "請在此填入" in HF_TOKEN or not HF_TOKEN.startswith("hf_"):
        st.error("🚨 致命錯誤：請先回到 GitHub 的程式碼第 11 行，填入您自己的 Hugging Face Token！")
    elif prompt.strip() == "":
        st.warning("⚠️ 請先輸入提示詞！")
    else:
        with st.spinner("✨ 正在呼叫專屬 AI 模型運算中，請稍候..."):
            try:
                # 透過後端發送標準的授權請求
                response = requests.post(
                    API_URL, 
                    headers=headers, 
                    json={"inputs": prompt},
                    timeout=60
                )
                
                # 狀況 1：成功產出圖片
                if response.status_code == 200:
                    image_bytes = response.content
                    st.image(image_bytes, caption=f"Prompt: {prompt}", use_container_width=True)
                    st.success("🎉 圖片生成成功！您可以對圖片點擊右鍵「另存圖片」。")
                    
                # 狀況 2：Hugging Face 的冷啟動機制 (這是正常的！)
                elif response.status_code == 503:
                    st.warning("⏳ 雲端 AI 模型正在開機喚醒中 (Estimated time: 約需 20~30 秒)。請不要離開畫面，稍等半分鐘後再次點擊「開始生成」按鈕即可！")
                    
                # 狀況 3：其他錯誤
                else:
                    st.error(f"🚨 API 發生異常 (錯誤碼: {response.status_code})：{response.text}")
                    
            except Exception as e:
                st.error(f"🚨 系統連線發生網路錯誤：{e}")
