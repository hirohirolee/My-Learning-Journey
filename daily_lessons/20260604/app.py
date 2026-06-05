import streamlit as st
import urllib.parse
import random

st.set_page_config(page_title="AI Generator", layout="wide")

st.title("🎨 AI 圖像生成 Web App")
prompt = st.text_area("請輸入提示詞 (Prompt):", placeholder="A cat walking on the beach...")
submit_button = st.button("開始生成", type="primary")

if submit_button and prompt.strip():
    # 這是最簡單的圖片網址，完全不需要後端連線，直接由瀏覽器發送請求
    encoded_prompt = urllib.parse.quote(prompt.strip())
    random_seed = random.randint(1, 99999)
    # 使用 pollinations.ai 直接渲染，這是一個公開且無需驗證的通道
    img_url = "https://image.pollinations.ai/prompt/" + encoded_prompt + "?seed=" + str(random_seed) + "&nologo=true&width=800&height=600"
    
    st.success("✨ 圖片已由前端渲染引擎載入！")
    # 直接由瀏覽器請求圖片，不經過 Streamlit 伺服器
    st.image(img_url, use_container_width=True)
    st.caption("若圖片無法顯示，請按右下角 Manage App -> Reboot App 後重新整理")
