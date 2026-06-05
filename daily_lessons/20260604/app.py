import streamlit as st
import streamlit.components.v1 as components
import json

# ==========================================
# 1. 網頁基本設定
# ==========================================
st.set_page_config(page_title="AI 圖像生成 Web App", page_icon="🎨", layout="wide")

# ==========================================
# 2. 安全地讀取系統預設 API Key
# ==========================================
try:
    system_hf_token = st.secrets["HF_TOKEN"]
except KeyError:
    system_hf_token = None

# ==========================================
# 3. 左側邊欄設計
# ==========================================
with st.sidebar:
    st.markdown("### 🛡️ 系統狀態")
    if system_hf_token:
        st.success("🟢 後端密鑰託管：正常")
    else:
        st.warning("⚠️ 後端密鑰託管：未設定")
        
    st.divider()
    user_hf_token = st.text_input("🔑 自訂 Hugging Face Token (選填):", type="password")
    
    if user_hf_token.strip():
        active_token = user_hf_token.strip()
    else:
        active_token = system_hf_token

    st.divider()
    selected_model = st.selectbox(
        "選擇 AI 模型:",
        (
            "black-forest-labs/FLUX.1-schnell", 
            "stabilityai/sdxl-turbo", 
            "stabilityai/stable-diffusion-xl-base-1.0"
        )
    )

# ==========================================
# 4. 主畫面設計
# ==========================================
st.title("🎨 AI 圖像生成 Web App")
st.markdown("**(🚀 終極防斷網版：透過您的瀏覽器前端直連 Hugging Face)**")

prompt = st.text_area("請輸入提示詞 (Prompt):", placeholder="A cat walking on the beach...", height=150)
submit_button = st.button("開始生成", type="primary")

# ==========================================
# 5. HTML 與 JS 樣板 (已優化行寬，防編輯器強制斷行)
# ==========================================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-white p-4">
    <div class="relative rounded-lg overflow-hidden bg-slate-100 min-h-[450px] border border-slate-300 flex items-center justify-center">
        
        <div id="status-box" class="flex flex-col items-center justify-center p-6 text-center">
            <svg class="w-12 h-12 text-blue-500 mb-4 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <p id="status-text" class="text-lg font-bold text-blue-700 animate-pulse">
                🚀 正在透過您的瀏覽器直連 Hugging Face...
            </p>
            <p id="sub-status" class="text-sm font-medium text-slate-500 mt-2">
                (已完美繞過 Streamlit 雲端機房，免疫斷網)
            </p>
        </div>
        
        <img id="result-image" src="" class="hidden w-full h-auto max-h-[550px] object-contain" alt="AI Image" />
        
    </div>
    
    <script>
        // 變數將由 Python 安全取代 (使用 JSON 確保字串安全)
        const P = __PROMPT__;
        const T = __TOKEN__;
        const M = __MODEL__;
        const apiUrl = "https://api-inference.huggingface.co/models/" + M;
        
        const statusBox = document.getElementById('status-box');
        const statusText = document.getElementById('status-text');
        const subStatus = document.getElementById('sub-status');
        const imgEl = document.getElementById('result-image');

        async function fetchImage() {
            try {
                let response = await fetch(apiUrl, {
                    method: 'POST',
                    headers: { 
                        'Authorization': 'Bearer ' + T, 
                        'Content-Type': 'application/json' 
                    },
                    body: JSON.stringify({inputs: P})
                });

                if (response.status === 503) {
                    const data = await response.json();
                    const waitTime = Math.max(Math.round(data.estimated_time || 20), 1);
                    statusText.innerText = "⏳ 模型休眠中，正在喚醒...";
                    statusText.className = "text-lg font-bold text-amber-600 animate-pulse";
                    subStatus.innerText = "預計等待 " + waitTime + " 秒，系統將自動重試...";
                    
                    // 自動倒數重試
                    setTimeout(fetchImage, Math.min(waitTime * 1000, 15000));
                    return;
                }

                if (!response.ok) {
                    const errText = await response.text();
                    statusText.innerText = "❌ 連線錯誤";
                    statusText.className = "text-lg font-bold text-red-600";
                    subStatus.innerText = "狀態碼: " + response.status + " | " + errText;
                    return;
                }

                // 成功取得圖片
                const blob = await response.blob();
                imgEl.src = URL.createObjectURL(blob);
                imgEl.classList.remove('hidden');
                statusBox.classList.add('hidden');
            } catch(e) {
                statusText.innerText = "❌ 網路連線失敗";
                statusText.className = "text-lg font-bold text-red-600";
                subStatus.innerText = e.message;
            }
        }
        
        // 啟動前端生圖
        fetchImage();
    </script>
</body>
</html>
"""

# ==========================================
# 6. 生成邏輯
# ==========================================
if submit_button:
    if not prompt.strip():
        st.warning("⚠️ 請輸入提示詞！")
    elif not active_token:
        st.error("⚠️ 無可用金鑰，請在左側輸入 Hugging Face Token！")
    else:
        st.success("📡 指令發送成功！正在呼叫瀏覽器直連引擎...")
        
        # 使用 replace 完美避開大括號衝突，使用 json.dumps 完美避開引號衝突
        html_code = HTML_TEMPLATE.replace("__PROMPT__", json.dumps(prompt.strip()))
        html_code = html_code.replace("__TOKEN__", json.dumps(active_token))
        html_code = html_code.replace("__MODEL__", json.dumps(selected_model))
        
        components.html(html_code, height=650, scrolling=False)
