import streamlit as st
import requests
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
st.caption("輸入文字，見證奇蹟 (Streamlit 原生版)")

# 讓使用者輸入 API Key (避免明碼寫在 GitHub 上，保護你的帳號安全)
API_KEY = st.text_input("請輸入您的 Gemini API Key (測試用):", type="password")

st.markdown("### 你想畫些什麼？")
prompt = st.text_area("提示詞", label_visibility="collapsed", placeholder="例如：一隻戴著太空頭盔的橘貓，正在火星上喝珍珠奶茶，高畫質...", height=100)

def fetch_with_retry(url, headers, json_data, retries=3):
    """實作簡單的網路重試機制"""
    delays = [2, 4, 8]
    for i in range(retries):
        try:
            response = requests.post(url, headers=headers, json=json_data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            if i == retries - 1:
                raise e
            time.sleep(delays[i])

# 生成按鈕
if st.button("✨ 立即生成圖片"):
    if not API_KEY:
        st.error("⚠️ 請先在上方輸入 API Key！")
    elif not prompt.strip():
        st.warning("⚠️ 請先輸入你想生成的圖片描述！")
    else:
        with st.spinner("魔法施展中，請稍候..."):
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-4.0-generate-001:predict?key={API_KEY}"
                headers = {'Content-Type': 'application/json'}
                payload = {
                    "instances": {"prompt": prompt.strip()},
                    "parameters": {"sampleCount": 1}
                }

                result = fetch_with_retry(url, headers, payload)

                if "predictions" in result and len(result["predictions"]) > 0:
                    base64_image = result["predictions"][0].get("bytesBase64Encoded")
                    if base64_image:
                        st.success("🎉 生成成功！")
                        # 顯示圖片
                        st.image(f"data:image/png;base64,{base64_image}", use_container_width=True)
                    else:
                        st.error("無法生成圖片。這通常是因為「提示詞觸發了安全審查機制」。請修改提示詞後再試一次！")
                elif "error" in result:
                    st.error(f"伺服器錯誤: {result['error'].get('message', '未知錯誤')}")
                else:
                    st.error("無法生成圖片，請修改提示詞後再試一次！")

            except Exception as e:
                st.error(f"連線或生成過程中發生錯誤：{e}")
