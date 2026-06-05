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
st.caption("HW3 作業展示版 (免 Key 穩定版 - 絕不塞車爆滿)")

# 3. 輸入區域
prompt = st.text_area("你想畫些什麼？", placeholder="例如：貓睡覺、在火星上喝咖啡的宇航員...", height=100)

# 4. 生成按鈕與邏輯
if st.button("✨ 立即生成圖片", type="primary"):
    if prompt.strip() != "":
        with st.spinner("魔法施展中，後端伺服器運算中..."):
            try:
                # 將中文提示詞轉為網址編碼，避免網址解析失敗
                # 提示：Pollinations AI 的模型對英文理解較佳，輸入英文效果會更棒喔！
                encoded_prompt = urllib.parse.quote(prompt)
                
                # 組裝完全免費的 Pollinations 繪圖 API 網址
                # 參數說明：width/height 控制尺寸, enhance=true 會自動優化擴寫提示詞以提升畫質
                image_url = f"https://image.pollinations.ai/p/{encoded_prompt}?width=800&height=600&enhance=true"
                
                # 展示圖片
                st.success("圖片生成成功！")
                st.image(image_url, caption=f"AI 根據「{prompt}」生成的作品", use_container_width=True)
                
                # 提供圖片網址讓使用者可以另存
                st.info(f"🔗 圖片直連網址：{image_url}")
                
            except Exception as e:
                st.error(f"遭遇未知錯誤：{str(e)}")
    else:
        st.warning("請填寫你想畫的內容描述喔！")

# 5. 系統狀態報告（優化原本的提示）
st.markdown("---")
with st.expander("💡 系統狀態報告"):
    st.write("● 本 Web App 目前串接 Pollinations 免費分布式運算端點，服務正常。")
    st.write("● 毋需綁定任何信用卡或 API Key，適合展示與學術作業使用。")
