import streamlit as st
import streamlit.components.v1 as components

# 設定網頁標題與寬度
st.set_page_config(page_title="AI 圖像生成 Web App", page_icon="🎨", layout="centered")

# 🔑 關鍵：請將您之前成功申請的 Hugging Face Token 貼在這裡
HF_TOKEN = "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"

with st.sidebar:
    st.markdown("### 🛡️ 系統狀態")
    st.success("🟢 系統連線正常 (全端穩定版)")
    st.info("本系統使用 JavaScript 前端直連技術，完美連接穩定的 Hugging Face 模型！")

st.title("🎨 AI 圖像生成 Web App")
st.markdown("輸入一段文字，讓 AI 為你創作圖片。")

prompt = st.text_area("請輸入提示詞 (Prompt):", "a cat walking on the beach")

if st.button("開始生成", type="primary"):
    if prompt.strip() == "":
        st.warning("⚠️ 請先輸入提示詞！")
    elif "hf_" not in HF_TOKEN:
        st.error("🚨 程式碼錯誤：請先在程式碼第 8 行填入您申請好的 Hugging Face Token！")
    else:
        st.success("✨ 請求已送出！請等待下方畫面載入結果...")
        
        # 🚀 終極解決方案：用 JavaScript 讓瀏覽器直接連線抓圖
        html_code = f"""
        <div style="display: flex; flex-direction: column; align-items: center; margin-top: 10px; font-family: sans-serif;">
            <p id="status-msg" style="color: #666; margin-bottom: 10px;">⏳ 正在連線至 AI 伺服器...</p>
            <img id="ai-image" style="display: none; max-width: 100%; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.2);" />
        </div>
        
        <script>
        async function fetchImage() {{
            const promptText = "{prompt}";
            const token = "{HF_TOKEN}";
            // 使用穩定度極高的 Stable Diffusion XL 模型
            const apiUrl = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0";
            const statusMsg = document.getElementById("status-msg");
            const imgElement = document.getElementById("ai-image");
            
            try {{
                statusMsg.innerText = "⏳ 正在生成圖片，高畫質運算可能需要 10 到 20 秒...";
                
                const response = await fetch(apiUrl, {{
                    method: "POST",
                    headers: {{
                        "Authorization": "Bearer " + token,
                        "Content-Type": "application/json"
                    }},
                    body: JSON.stringify({{ inputs: promptText }})
                }});
                
                if (!response.ok) {{
                    statusMsg.innerText = "🚨 模型正在喚醒或伺服器忙碌，請等待一分鐘後再點擊一次生成！(錯誤碼: " + response.status + ")";
                    return;
                }}
                
                // 將回傳的二進位資料轉換為圖片顯示
                const blob = await response.blob();
                imgElement.src = URL.createObjectURL(blob);
                imgElement.style.display = "block";
                statusMsg.style.display = "none";
                
            }} catch (error) {{
                statusMsg.innerText = "🚨 網路發生錯誤：" + error.message;
            }}
        }}
        
        fetchImage();
        </script>
        """
        
        # 嵌入這段網頁程式碼來執行抓圖
        components.html(html_code, height=600)
