import streamlit as st
import urllib.parse
import random

st.set_page_config(page_title="AI Generator", layout="wide")

st.title("🎨 AI 圖像生成 Web App")
prompt = st.text_area("請輸入提示詞 (Prompt):", placeholder="A cat walking on the beach...")
submit_button = st.button("開始生成", type="primary")

if submit_button and prompt.strip():
    encoded_prompt = urllib.parse.quote(prompt.strip())
    random_seed = random.randint(1, 99999)
    img_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?seed={random_seed}&nologo=true"
    
    st.info("✨ 圖片正透過強制渲染模式注入...")
    
    # 這是最後的招式：使用 st.markdown 的 unsafe_allow_html=True
    # 這會直接在頁面上寫入 HTML，完全跳過 Streamlit 的圖像驗證邏輯
    st.markdown(
        f'<img src="{img_url}" style="width:100%; border-radius:15px; box-shadow:0 4px 10px rgba(0,0,0,0.2);">'
        , unsafe_allow_html=True
    )
    st.caption("如果依然看不到圖，請點擊下方 Manage App -> Reboot App 進行最後的伺服器環境清理。")
