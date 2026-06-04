import streamlit as st
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
st.caption("輸入文字，見證奇蹟 (Hugging Face 終極穩定版)")

# 💡 終極解法：直接把你的 Token 貼在這裡的引號裡面！
# 例如：HF_TOKEN = "hf_AbCdEfGhIjKlMnOpQrStUvWxYz"
HF_TOKEN = "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"

st.markdown("### 你想畫些什麼？")
prompt = st.text_area("提示詞", label_visibility="collapsed", placeholder="例如：A cute cat on the grass drinking cola, high quality...", height=100)
st.caption("💡 小提示：開源模型對英文的理解力更好，建議輸入英文提示詞喔！")

# 生成按鈕
if st.button("✨ 立即生成圖片"):
    if HF_TOKEN == "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" or not HF_TOKEN.startswith("hf_"):
        st.error("⚠️ 程式碼裡的 Token 好像還沒替換喔！請回到 GitHub 把 HF_TOKEN 換成你的密碼。")
    elif not prompt.strip():
        st.warning("⚠️ 請先輸入你想生成的圖片描述！")
    else:
        with st.spinner("魔法施展中，大約需要 15~30 秒，請稍候..."):
            try:
                # 使用 Hugging Face 官方穩定的生圖模型
                API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
                headers = {"Authorization": f"Bearer {HF_TOKEN}"}
                
                payload = {"inputs": prompt.strip()}
                response = requests.post(API_URL, headers=headers, json=payload, timeout=45)
                
                if response.status_code == 200:
                    st.success("🎉 生成成功！")
                    st.image(response.content, use_container_width=True)
                elif response.status_code == 503:
                    st.warning("模型正在暖機中，請等待約 30 秒後，再點擊一次「立即生成圖片」！")
                else:
                    st.error(f"圖片生成失敗 (錯誤碼: {response.status_code})。")
                    
            except requests.exceptions.Timeout:
                st.error("伺服器畫圖畫太久了，發生超時錯誤，請稍後再試一次！")
            except Exception as e:
                st.error(f"生圖過程中發生錯誤：{e}")
