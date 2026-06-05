import streamlit as st
import urllib.parse

# 1. 網頁基本設定
st.set_page_config(
    page_title="AI 魔法生圖器",
    page_icon="✨",
    layout="centered"
)

# 2. 標題與簡介
st.title("✨ AI 魔法生圖器")
st.caption("HW3 作業展示版 (免 Key 穩定修復版)")

# 3. 輸入區域
prompt = st.text_area("你想畫些什麼？", placeholder="例如：貓睡覺 喝可樂...", height=100)

# 4. 生成按鈕與邏輯
if st.button("✨ 立即生成圖片", type="primary"):
    # 關鍵防錯：使用 .strip() 去除前後的換行與空白
    clean_prompt = prompt.strip()
    
    if clean_prompt != "":
        with st.spinner("魔法施展中，後端伺服器運算中..."):
            try:
                # 關鍵防錯二：將內文所有的換行字元 \n 全部替換成標準空白，徹底杜絕 %0A 造成的 404 錯誤
                clean_prompt = clean_prompt.replace('\n', ' ')
                
                # 將清洗後的中文提示詞轉為網址編碼
                encoded_prompt = urllib.parse.quote(clean_prompt)
                
                # 組裝 Pollinations 繪圖 API 網址
                image_url = f"https://image.pollinations.ai/p/{encoded_prompt}?width=800&height=600&enhance=true"
                
                # 展示圖片
                st.success("圖片生成成功！")
                st.image(image_url, caption=f"AI 根據「{clean_prompt}」生成的作品", use_container_width=True)
                
                # 提供圖片網址
                st.info(f"🔗 圖片直連網址：{image_url}")
                
            except Exception as e:
                st.error(f"遭遇未知錯誤：{str(e)}")
    else:
        st.warning("請填寫你想畫的內容描述喔！")

# 5. 系統狀態報告
st.markdown("---")
with st.expander("💡 系統狀態報告"):
    st.write("● 本 Web App 已補上文字清洗機制，自動過濾掉干擾網址解析的換行符號 (%0A)。")
    st.write("● 毋需綁定任何信用卡或 API Key，適合展示與學術作業使用。")
