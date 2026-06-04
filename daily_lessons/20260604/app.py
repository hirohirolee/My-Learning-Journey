import streamlit as st
import urllib.parse
import time
import requests

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
        with st.spinner("魔法施展中，這大約需要 5~10 秒，請稍候..."):
            try:
                # 處理中文與特殊符號，確保網址正確
                safe_prompt = urllib.parse.quote(prompt.strip())
                seed = int(time.time())
                image_url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width=1024&height=1024&nologo=true&seed={seed}"
                
                # 💡 關鍵修正：加上 User-Agent 標頭，偽裝成 Chrome 瀏覽器，避免被伺服器阻擋
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                }
                
                # 發送帶有偽裝標頭的請求
                response = requests.get(image_url, headers=headers, timeout=30)
                
                if response.status_code == 200:
                    st.success("🎉 生成成功！")
                    st.image(response.content, use_container_width=True)
                else:
                    # 顯示具體的錯誤代碼，方便追蹤
                    st.error(f"圖片生成失敗 (錯誤碼: {response.status_code})，請稍後再試一次！")
                    
            except requests.exceptions.Timeout:
                st.error("伺服器畫圖畫太久了，發生超時錯誤，請再試一次！")
            except Exception as e:
                st.error(f"生圖過程中發生錯誤：{e}")
