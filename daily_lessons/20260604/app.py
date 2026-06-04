import streamlit as st
import urllib.parse
import time

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
st.caption("輸入文字，見證奇蹟 (免密碼極簡版)")

st.markdown("### 你想畫些什麼？")
prompt = st.text_area("提示詞", label_visibility="collapsed", placeholder="例如：一隻戴著太空頭盔的橘貓，正在火星上喝珍珠奶茶，高畫質...", height=100)

# 生成按鈕
if st.button("✨ 立即生成圖片"):
    if not prompt.strip():
        st.warning("⚠️ 請先輸入你想生成的圖片描述！")
    else:
        with st.spinner("魔法施展中，大約需要 5~10 秒，請稍候..."):
            
            # 處理文字與亂數種子
            safe_prompt = urllib.parse.quote(prompt.strip())
            seed = int(time.time())
            
            # 使用完全免費免 Key 的 Pollinations 服務
            image_url = f"https://image.pollinations.ai/prompt/{safe_prompt}?nologo=true&seed={seed}"
            
            st.success("🎉 生成指令已送出！")
            
            # 嘗試用 Markdown 直接顯示圖片
            st.markdown(f"![AI 生成圖片]({image_url})")
            
            # 備用保險機制：提供直接外連的按鈕 (交作業必備)
            st.info("💡 如果上方沒有馬上顯示圖片，請點擊下方按鈕直接查看：")
            st.markdown(f"""
                <a href="{image_url}" target="_blank" style="display: block; text-align: center; background-color: #10B981; color: white; padding: 12px; border-radius: 10px; text-decoration: none; font-weight: bold;">
                    🔗 在新分頁開啟生成的圖片
                </a>
            """, unsafe_allow_html=True)
