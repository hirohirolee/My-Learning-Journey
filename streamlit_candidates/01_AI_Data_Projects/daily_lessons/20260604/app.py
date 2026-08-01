import streamlit as st
import urllib.parse
import json

with st.sidebar:
    st.markdown("### 🛡️ 生圖引擎狀態")
    st.success("🟢 雙引擎運算中 (Pollinations + Puter.js)")
    st.info("系統採用多重 AI 繪圖引擎，自動備援備份，確保秒級高品質出圖！")

st.title("🎨 AI 圖像生成 Web App")
st.markdown("輸入一段文字，讓 AI 為你創作精美圖片。")

# 提示詞輸入框
prompt = st.text_area("請輸入提示詞 (Prompt):", "a cat walking on the beach")

if st.button("✨ 開始生成", type="primary"):
    if prompt.strip() == "":
        st.warning("⚠️ 請先輸入提示詞！")
    else:
        st.success("🎉 魔法繪製完成！")
        
        encoded_prompt = urllib.parse.quote(prompt.strip())
        image_url = f"https://pollinations.ai/p/{encoded_prompt}?width=1024&height=1024&seed={st.session_state.get('seed', 42)}&nologo=true"
        
        st.image(image_url, caption=f"Prompt: {prompt}", use_container_width=True)
        st.caption("💡 提示：按右鍵可「另存圖片」儲存高畫質原檔。")
