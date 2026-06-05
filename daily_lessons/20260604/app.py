import streamlit as st
import urllib.parse
import random

# 設定網頁標題
st.set_page_config(page_title="AI 圖像生成 Web App", page_icon="🎨", layout="centered")

st.title("🎨 AI 圖像生成 Web App")
st.markdown("輸入一段文字，讓 AI 為你創作圖片。")

prompt = st.text_area("請輸入提示詞 (Prompt):", "a cat walking on the beach")

if st.button("開始生成", type="primary"):
    if prompt.strip() == "":
        st.warning("⚠️ 請先輸入提示詞！")
    else:
        with st.spinner("✨ 雲端 AI 正在努力作畫中，請耐心稍候 (約需 5-10 秒)..."):
            # 將提示詞轉換為網址安全格式
            encoded_prompt = urllib.parse.quote(prompt)
            seed = random.randint(1, 1000000)
            
            # 使用開發者專用的免金鑰生圖 API
            image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true&seed={seed}"
            
            # 🚀 終極殺手鐧：直接傳遞網址給 st.image
            # 這會強制您的瀏覽器自己去下載圖片，完全避開伺服器斷網問題
            st.image(image_url, caption=f"Prompt: {prompt}", use_container_width=True)
            st.success("🎉 圖片生成成功！您可以對圖片點擊右鍵「另存圖片」。")
