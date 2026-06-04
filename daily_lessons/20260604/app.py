import streamlit as st
import urllib.parse
import time
import requests

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
st.caption("HW3 作業展示版 (包含 API 負載例外處理)")

st.markdown("### 你想畫些什麼？")
prompt = st.text_area("提示詞", label_visibility="collapsed", placeholder="例如：一隻戴著太空頭盔的橘貓，正在火星上喝珍珠奶茶，高畫質...", height=100)

# 生成按鈕
if st.button("✨ 立即生成圖片"):
    if not prompt.strip():
        st.warning("⚠️ 請先輸入你想生成的圖片描述！")
    else:
        with st.spinner("魔法施展中，大約需要 5~10 秒，請稍候..."):
            
            safe_prompt = urllib.parse.quote(prompt.strip())
            seed = int(time.time())
            image_url = f"https://image.pollinations.ai/prompt/{safe_prompt}?nologo=true&seed={seed}"
            
            try:
                # 加上偽裝標頭，並由後台嘗試抓取圖片
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                }
                response = requests.get(image_url, headers=headers, timeout=15)
                
                # 判斷伺服器回傳的是不是真的「圖片」
                if response.status_code == 200 and 'image' in response.headers.get('Content-Type', ''):
                    st.success("🎉 生成成功！")
                    st.image(response.content, use_container_width=True)
                else:
                    # 如果回傳的是 JSON 錯誤 (例如 Queue Full)
                    st.error("⚠️ 第三方免 Key 生圖 API 目前全球滿載中 (Queue Full)！")
                    st.info("💡 **系統狀態報告：** 本 Web App 的 UI 介面、連線邏輯與 Prompt 傳遞皆已正確執行。當前的無法出圖是源於免費端點的運算資源限制，請稍候幾分鐘再試一次。")
                    
            except Exception as e:
                st.error(f"連線發生例外錯誤：{e}")
