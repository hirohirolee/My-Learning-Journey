import streamlit as st

# 設定網頁標題
st.set_page_config(page_title="AI 圖像生成 Web App", page_icon="🎨", layout="centered")

st.title("🎨 AI 圖像生成 Web App")
st.markdown("為確保系統穩定，本服務已無縫橋接 Hugging Face 官方運算節點。請在下方輸入英文提示詞：")

# 直接嵌入 Hugging Face 的 FLUX 模型官方介面
st.components.v1.iframe("https://black-forest-labs-flux-1-schnell.hf.space", height=800, scrolling=True)
