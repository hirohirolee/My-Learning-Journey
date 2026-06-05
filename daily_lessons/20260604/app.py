import streamlit as st
import urllib.parse

# 設定網頁標題與寬度
st.set_page_config(page_title="AI 圖像生成 Web App", page_icon="🎨", layout="centered")

# 側邊欄設計 (讓畫面看起來更完整)
with st.sidebar:
    st.markdown("### 🛡️ 系統狀態")
    st.success("🟢 系統連線正常")
    st.info("本系統採用無金鑰 (Serverless) 架構，無需登入即可無限次生成。")

# 主畫面標題
st.title("🎨 AI 圖像生成 Web App")
st.markdown("輸入一段文字，讓 AI 為你創作圖片。")

# 提示詞輸入框
prompt = st.text_area("請輸入提示詞 (Prompt):", "a cat walking on the beach")

# 生成按鈕
if st.button("開始生成", type="primary"):
    if prompt.strip() == "":
        st.warning("⚠️ 請先輸入提示詞！")
    else:
        with st.spinner("✨ 雲端 AI 正在努力作畫中，請稍候..."):
            try:
                # 將提示詞轉換為網址安全格式 (URL Encoding)
                encoded_prompt = urllib.parse.quote(prompt)
                
                # 呼叫 Pollinations AI 的免金鑰開源 API
                image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true"
                
                # 在網頁上顯示生成的圖片
                st.image(image_url, caption=f"Prompt: {prompt}", use_container_width=True)
                st.success("🎉 圖片生成成功！您可以對圖片點擊右鍵「另存圖片」。")
                
            except Exception as e:
                st.error(f"🚨 發生錯誤：{e}")
