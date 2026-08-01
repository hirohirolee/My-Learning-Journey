import streamlit as st
import streamlit.components.v1 as components
import json

# 側邊欄設計
with st.sidebar:
    st.markdown("### 🛡️ 系統狀態")
    st.success("🟢 系統連線正常 (Puter直連版)")
    st.info("本系統已升級至最穩定的 Puter.js 前端渲染技術，完美繞過所有伺服器阻擋！")

st.title("🎨 AI 圖像生成 Web App")
st.markdown("輸入一段文字，讓 AI 為你創作圖片。")

# 提示詞輸入框
prompt = st.text_area("請輸入提示詞 (Prompt):", "a cat walking on the beach")

# 生成按鈕
if st.button("開始生成", type="primary"):
    if prompt.strip() == "":
        st.warning("⚠️ 請先輸入提示詞！")
    else:
        st.success("✨ 請求已送出！魔法繪製中，請稍候...")

        # 將提示詞轉換為 JSON 格式，確保傳遞給 JavaScript 時不會因引號產生錯誤
        prompt_json = json.dumps(prompt)

        # 🚀 借鏡同學程式碼中最成功的核心技術：Puter.js 前端直連
        puter_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <script src="https://js.puter.com/v2/"></script>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    color: #333;
                }}
                .loader {{
                    border: 4px solid #f3f3f3;
                    border-top: 4px solid #10b981;
                    border-radius: 50%;
                    width: 50px;
                    height: 50px;
                    animation: spin 1s linear infinite;
                    margin-bottom: 15px;
                }}
                @keyframes spin {{
                    0% {{ transform: rotate(0deg); }}
                    100% {{ transform: rotate(360deg); }}
                }}
            </style>
        </head>
        <body>
            <div id="loading" style="text-align: center; margin-top: 30px;">
                <div class="loader" style="margin: 0 auto;"></div>
                <p style="color: #666; font-weight: bold; font-size: 1.1em;">⏳ 正在透過瀏覽器呼叫 AI 模型...</p>
                <p style="color: #999; font-size: 0.9em;">高畫質運算約需 10 到 20 秒，請耐心等候</p>
            </div>
            
            <div id="result" style="display: none; width: 100%; text-align: center; margin-top: 10px;">
                <img id="ai-image" style="max-width: 100%; border-radius: 12px; box-shadow: 0 6px 12px rgba(0,0,0,0.15);" />
                <p style="color: #10b981; font-weight: bold; margin-top: 15px;">🎉 圖片生成成功！請在圖片上點擊右鍵「另存圖片」</p>
            </div>

            <script>
                async function generateImage() {{
                    const promptText = {prompt_json};
                    try {{
                        // 呼叫 Puter.js 的內建 AI 生圖 (預設為 Stable Diffusion XL)
                        const result = await puter.ai.txt2img(promptText, {{
                            model: "stabilityai/stable-diffusion-xl-base-1.0"
                        }});
                        
                        if (result && result.src) {{
                            // 將生成的圖片放入 img 標籤中
                            document.getElementById('ai-image').src = result.src;
                            
                            // 隱藏載入動畫，顯示圖片
                            document.getElementById('loading').style.display = 'none';
                            document.getElementById('result').style.display = 'block';
                        }} else {{
                            throw new Error("AI 伺服器未回傳圖片");
                        }}
                    }} catch (error) {{
                        // 錯誤處理機制
                        document.getElementById('loading').innerHTML = `
                            <span style="font-size: 3rem;">⚠️</span>
                            <p style="color: #ef4444; font-weight: bold; font-size: 1.2em; margin-top: 10px;">生成失敗</p>
                            <p style="color: #666; font-size: 0.9em;">${{error.message || '網路連線逾時'}}</p>
                            <p style="color: #999; font-size: 0.8em; margin-top: 10px;">請確認網路連線正常，或稍後再重新點擊生成按鈕。</p>
                        `;
                    }}
                }}
                
                // 啟動執行
                generateImage();
            </script>
        </body>
        </html>
        """
        
        # 將這段帶有 Puter.js 技術的 HTML 嵌入您的 Streamlit 網頁中
        components.html(puter_html, height=600, scrolling=True)
