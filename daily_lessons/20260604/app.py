import streamlit as st
import urllib.parse
import time
import streamlit.components.v1 as components

# 設定網頁標題與排版
st.set_page_config(page_title="AI 魔法生圖器", page_icon="✨", layout="centered")

# 自訂 CSS
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        border-radius: 15px;
        height: 50px;
        font-weight: bold;
        background-color: #4F46E5;
        color: white;
    }
    .stButton>button:hover {
        background-color: #4338CA;
        color: white;
    }
    .stTextInput>div>div>input, .stTextArea>div>div>textarea {
        border-radius: 15px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("✨ AI 魔法生圖器")
st.caption("輸入文字，見證奇蹟 (前端直連免 Key 版)")

st.markdown("### 你想畫些什麼？")
prompt = st.text_area("提示詞", label_visibility="collapsed", placeholder="例如：一隻戴著太空頭盔的橘貓，正在火星上喝珍珠奶茶，高畫質...", height=100)

# 生成按鈕
if st.button("✨ 立即生成圖片"):
    if not prompt.strip():
        st.warning("⚠️ 請先輸入你想生成的圖片描述！")
    else:
        with st.spinner("魔法施展中，這大約需要 10~20 秒，請稍候..."):
            
            # 處理中文與特殊符號，確保網址正確
            safe_prompt = urllib.parse.quote(prompt.strip())
            seed = int(time.time())
            
            # 使用 Pollinations 穩定的生圖網址
            image_url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width=1024&height=1024&nologo=true&seed={seed}"
            
            # 💡 關鍵架構轉換：使用 HTML img 標籤，把讀取圖片的工作轉交給「使用者的瀏覽器」
            # 這能完美避開 Streamlit 雲端 IP 被阻擋 (402) 的問題，也解決了破圖問題。
            html_code = f"""
            <div style="display: flex; justify-content: center; align-items: center; width: 100%; padding: 10px;">
                <img src="{image_url}" style="width: 100%; max-width: 512px; border-radius: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);" alt="AI 正在努力畫圖中，請稍候幾秒鐘...">
            </div>
            """
            
            # 在 Streamlit 中嵌入並執行這段 HTML
            components.html(html_code, height=600)
            
            st.success("🎉 指令已發送！(請等待瀏覽器將圖片載入顯示)")
