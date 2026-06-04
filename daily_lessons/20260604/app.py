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
st.caption("輸入文字，見證奇蹟 (直連抗阻擋版)")

st.markdown("### 你想畫些什麼？")
prompt = st.text_area("提示詞", label_visibility="collapsed", placeholder="例如：一隻戴著太空頭盔的橘貓，正在火星上喝珍珠奶茶，高畫質...", height=100)

# 生成按鈕
if st.button("✨ 立即生成圖片"):
    if not prompt.strip():
        st.warning("⚠️ 請先輸入你想生成的圖片描述！")
    else:
        with st.spinner("魔法施展中，大約需要 10 秒，請稍候..."):
            
            # 處理中文與特殊符號
            safe_prompt = urllib.parse.quote(prompt.strip())
            seed = int(time.time())
            
            # 簡化網址，減少被伺服器誤判的機率
            image_url = f"https://image.pollinations.ai/prompt/{safe_prompt}?seed={seed}"
            
            st.success("🎉 生成指令已送出！")
            
            # 💡 解法 1：使用 Streamlit 內建 Markdown 渲染圖片，避開 iframe 隔離限制
            st.markdown(f"![AI 生成圖片]({image_url})")
            
            # 💡 解法 2：如果瀏覽器依然嚴格阻擋載入，提供直接外連的備用按鈕 (交作業必備)
            st.info("💡 如果上方沒有顯示圖片 (被瀏覽器阻擋)，請點擊下方按鈕直接查看：")
            st.markdown(f"""
                <a href="{image_url}" target="_blank" style="display: block; text-align: center; background-color: #10B981; color: white; padding: 12px; border-radius: 10px; text-decoration: none; font-weight: bold;">
                    🔗 在新分頁開啟生成的圖片
                </a>
            """, unsafe_allow_html=True)
