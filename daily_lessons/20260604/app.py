import streamlit as st
import urllib.parse
import time

# 設定網頁標題與排版
st.set_page_config(page_title="AI 魔法生圖器", page_icon="✨", layout="centered")

# 自訂 CSS 讓按鈕和畫面更像手機 App
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
st.caption("輸入文字，見證奇蹟 (免 Key 穩定版)")

st.markdown("### 你想畫些什麼？")
prompt = st.text_area("提示詞", label_visibility="collapsed", placeholder="例如：一隻戴著太空頭盔的橘貓，正在火星上喝珍珠奶茶，高畫質...", height=100)

# 生成按鈕
if st.button("✨ 立即生成圖片"):
    if not prompt.strip():
        st.warning("⚠️ 請先輸入你想生成的圖片描述！")
    else:
        with st.spinner("魔法施展中，請稍候..."):
            try:
                # 處理中文與特殊符號，確保網址正確
                safe_prompt = urllib.parse.quote(prompt.strip())
                
                # 加入隨機的種子碼 (seed)，確保就算輸入一樣的文字，每次也能產生新的圖片
                seed = int(time.time())
                
                # 呼叫開源 Text2Image API
                image_url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width=1024&height=1024&nologo=true&seed={seed}"
                
                st.success("🎉 生成成功！")
                
                # 讓 Streamlit 直接載入並顯示圖片
                st.image(image_url, use_container_width=True)
            except Exception as e:
                st.error(f"生圖過程中發生錯誤：{e}")
