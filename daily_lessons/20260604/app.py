import streamlit as st
import requests

# 設定網頁標題與寬度
st.set_page_config(page_title="AI 圖像生成 Web App", page_icon="🎨", layout="centered")

# 🔑 關鍵步驟：將您剛才在 Hugging Face 申請的 Token 貼在這裡
# 這樣網頁的使用者就完全不需要登入，由這組 Token 在後台代為授權！
HF_TOKEN = "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" 

# 使用穩定度極高的 Stable Diffusion XL 模型
API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
headers = {"Authorization": f"Bearer {HF_TOKEN}"}

# 側邊欄設計
with st.sidebar:
    st.markdown("### 🛡️ 系統狀態")
    st.success("🟢 系統連線正常")
    st.info("本系統已內建專屬 API 授權，使用者無需登入即可直接生成高品質圖片。")

# 主畫面
st.title("🎨 AI 圖像生成 Web App")
st.markdown("輸入一段文字，讓 AI 為你創作圖片。")

prompt = st.text_area("請輸入提示詞 (Prompt):", "a cat walking on the beach")

if st.button("開始生成", type="primary"):
    if prompt.strip() == "":
        st.warning("⚠️ 請先輸入提示詞！")
    elif HF_TOKEN == "請把您的_hf_開頭的Token貼在這裡":
        st.error("🚨 程式碼錯誤：您忘記把 hf_ 開頭的 Token 貼到程式碼第 9 行了！")
    else:
        with st.spinner("✨ 雲端 AI 正在努力作畫中，請耐心稍候..."):
            try:
                # 呼叫 Hugging Face API
                response = requests.post(
                    API_URL, 
                    headers=headers, 
                    json={"inputs": prompt}
                )
                
                # 檢查伺服器回應
                if response.status_code == 200:
                    st.image(response.content, caption=f"Prompt: {prompt}", use_container_width=True)
                    st.success("🎉 圖片生成成功！請在圖片上點擊右鍵「另存圖片」。")
                else:
                    st.error(f"🚨 API 回應錯誤 ({response.status_code}): {response.text}")
                    
            except Exception as e:
                st.error(f"🚨 發生網路錯誤：{e}")
