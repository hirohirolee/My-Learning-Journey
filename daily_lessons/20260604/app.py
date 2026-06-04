import streamlit as st
import urllib.parse
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
st.caption("輸入文字，見證奇蹟 (Hercai 完全免費免 Key 版)")

st.markdown("### 你想畫些什麼？")
prompt = st.text_area("提示詞", label_visibility="collapsed", placeholder="例如：一隻戴著太空頭盔的橘貓，正在火星上喝珍珠奶茶，高畫質...", height=100)

# 生成按鈕
if st.button("✨ 立即生成圖片"):
    if not prompt.strip():
        st.warning("⚠️ 請先輸入你想生成的圖片描述！")
    else:
        with st.spinner("魔法施展中，這大約需要 10~15 秒，請稍候..."):
            try:
                # 處理中文與特殊符號，確保網址正確
                safe_prompt = urllib.parse.quote(prompt.strip())
                
                # 呼叫 Hercai 免費生圖 API (專為免 Key 設計的服務)
                api_url = f"https://hercai.onrender.com/v3/text2image?prompt={safe_prompt}"
                
                # 發送請求並設定超時保護
                response = requests.get(api_url, timeout=45)
                
                if response.status_code == 200:
                    data = response.json()
                    # 檢查回傳的 JSON 中是否有順利產生圖片網址
                    if "url" in data and data["url"]:
                        st.success("🎉 生成成功！")
                        # 顯示生成的圖片
                        st.image(data["url"], use_container_width=True)
                    else:
                        st.error("API 回傳格式異常，請稍後再試。")
                else:
                    st.error(f"圖片生成失敗 (錯誤碼: {response.status_code})，請稍後再試一次！")
                    
            except requests.exceptions.Timeout:
                st.error("伺服器畫圖畫太久了，發生超時錯誤，請再試一次！")
            except Exception as e:
                st.error(f"生圖過程中發生錯誤：{e}")
