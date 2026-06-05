import streamlit as st
import urllib.parse
import requests
import random  # 新增：用來產生隨機數

# 設定網頁標題與寬度
st.set_page_config(page_title="AI 圖像生成 Web App", page_icon="🎨", layout="centered")

with st.sidebar:
    st.markdown("### 🛡️ 系統狀態")
    st.success("🟢 系統連線正常")
    st.info("本系統採用無金鑰 (Serverless) 架構，無需登入即可無限次生成。")

st.title("🎨 AI 圖像生成 Web App")
st.markdown("輸入一段文字，讓 AI 為你創作圖片。")

prompt = st.text_area("請輸入提示詞 (Prompt):", "a cat walking on the beach")

if st.button("開始生成", type="primary"):
    if prompt.strip() == "":
        st.warning("⚠️ 請先輸入提示詞！")
    else:
        with st.spinner("✨ 雲端 AI 正在努力作畫中，請耐心稍候 (約需 5-10 秒)..."):
            try:
                encoded_prompt = urllib.parse.quote(prompt)
                
                # 加上隨機種子，確保每次生成的圖片都不一樣
                seed = random.randint(1, 1000000)
                image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true&seed={seed}"
                
                # 關鍵修改：設定 Headers，偽裝成正常的 Google Chrome 瀏覽器
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
                }
                
                # 送出請求時帶上偽裝的 Headers
                response = requests.get(image_url, headers=headers)
                
                # 檢查伺服器是否同意給圖
                if response.status_code == 200:
                    st.image(response.content, caption=f"Prompt: {prompt}", use_container_width=True)
                    st.success("🎉 圖片生成成功！您可以對圖片點擊右鍵「另存圖片」。")
                else:
                    st.error(f"🚨 AI 伺服器暫時阻擋了連線 (錯誤碼: {response.status_code})，請稍後再試一次！")
                
            except Exception as e:
                st.error(f"🚨 發生網路錯誤：{e}")
