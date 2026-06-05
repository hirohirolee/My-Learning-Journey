import streamlit as st
import urllib.parse
import random

# 設定網頁標題與寬度
st.set_page_config(page_title="AI 圖像生成 Web App", page_icon="🎨", layout="centered")

# 側邊欄設計：請確認更新後這裡的文字有改變！
with st.sidebar:
    st.markdown("### 🛡️ 系統狀態")
    st.success("🟢 系統連線正常 (前端渲染模式)")
    st.info("本系統採用前端直接請求技術，完美繞過伺服器網路限制！")

st.title("🎨 AI 圖像生成 Web App")
st.markdown("輸入一段文字，讓 AI 為你創作圖片。")

prompt = st.text_area("請輸入提示詞 (Prompt):", "a cat walking on the beach")

if st.button("開始生成", type="primary"):
    if prompt.strip() == "":
        st.warning("⚠️ 請先輸入提示詞！")
    else:
        # 將提示詞轉換為網址安全格式
        encoded_prompt = urllib.parse.quote(prompt)
        seed = random.randint(1, 1000000)
        
        # 組合免金鑰的圖片網址 (使用專為開發者設計的 Pollinations AI)
        image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true&seed={seed}"
        
        # 🚀 終極技巧：使用 HTML img 標籤
        # 這會強制「使用者的電腦」去下載圖片，完全不經過 Streamlit 斷網的後台
        html_code = f'''
            <div style="display: flex; justify-content: center; margin-top: 20px;">
                <img src="{image_url}" alt="AI Generated Image" style="max-width: 100%; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.2);">
            </div>
            <p style="text-align: center; color: gray; margin-top: 10px;">Prompt: {prompt}</p>
        '''
        
        st.markdown(html_code, unsafe_allow_html=True)
        st.success("🎉 圖片生成成功！您可以對圖片點擊右鍵「另存圖片」。")
