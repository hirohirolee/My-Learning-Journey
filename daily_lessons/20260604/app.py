import streamlit as st
import requests
import urllib.parse

# 設定網頁標題與寬度
st.set_page_config(page_title="AI 圖像生成 Web App", page_icon="🎨", layout="centered")

st.title("🎨 AI 圖像生成 Web App")
st.markdown("輸入一段文字，讓 AI 為你創作圖片。")

# 提示詞輸入框
prompt = st.text_area("請輸入提示詞 (Prompt):", "a cat walking on the beach")

# 生成按鈕
if st.button("開始生成", type="primary"):
    if prompt.strip() == "":
        st.warning("⚠️ 請先輸入提示詞！")
    else:
        with st.spinner("✨ 雲端 AI 正在努力作畫中，請耐心稍候 (約需 10-15 秒)..."):
            try:
                # 將提示詞轉換為網址安全格式
                encoded_prompt = urllib.parse.quote(prompt)
                
                # 💡 終極方案：使用專為開發者設計、無跨域阻擋的 Hercai API
                api_url = f"https://hercai.onrender.com/v3/text2image?prompt={encoded_prompt}"
                
                # 透過後端發送請求 (設定 timeout 避免無窮等待)
                response = requests.get(api_url, timeout=60)
                
                if response.status_code == 200:
                    data = response.json()
                    # 確認 API 有成功回傳圖片的 URL
                    if "url" in data and data["url"]:
                        # 使用回傳的真實圖片網址來顯示
                        st.image(data["url"], caption=f"Prompt: {prompt}", use_container_width=True)
                        st.success("🎉 圖片生成成功！您可以對圖片點擊右鍵「另存圖片」。")
                    else:
                        st.error("🚨 API 伺服器有回應，但未能順利產出圖片連結，請稍後再試。")
                else:
                    st.error(f"🚨 API 伺服器目前忙碌中 (錯誤碼: {response.status_code})，請稍候再點擊一次！")
                    
            except requests.exceptions.RequestException as e:
                st.error(f"🚨 系統連線超時或發生網路錯誤：{e}")
