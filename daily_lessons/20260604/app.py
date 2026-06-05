import streamlit as st
import streamlit.components.v1 as components
import json

# ==========================================
# 1. 網頁基本設定
# ==========================================
st.set_page_config(
    page_title="AI 圖像生成 Web App",
    page_icon="🎨",
    layout="wide"
)

# ==========================================
# 2. 安全地讀取系統預設 API Key (後端自動託管)
# ==========================================
try:
    system_hf_token = st.secrets["HF_TOKEN"]
except KeyError:
    system_hf_token = None

# ==========================================
# 3. 左側邊欄設計 (自訂密鑰雙軌機制)
# ==========================================
with st.sidebar:
    st.markdown("### 🛡️ 系統金鑰託管狀態")
    if system_hf_token:
        st.success("🟢 系統預設憑證：已於後端安全託管")
    else:
        st.warning("⚠️ 系統預設憑證：未偵測到後端託管")
        
    st.divider()
    
    st.markdown("### 🔑 使用者自訂密鑰 (選填)")
    user_hf_token = st.text_input(
        "輸入您的 Hugging Face Token:",
        type="password",
        placeholder="hf_...",
        help="留空將自動啟用系統後端託管憑證生圖"
    )
    
    if user_hf_token.strip():
        active_token = user_hf_token.strip()
        st.info("🔐 當前連線狀態：已啟用您輸入的自訂密鑰")
    else:
        active_token = system_hf_token
        if system_hf_token:
            st.info("🔒 當前連線狀態：已啟用後端自動託管憑證")
        else:
            st.error("❌ 當前連線狀態：無可用憑證，將無法生圖")

    st.divider()
    st.markdown("### ⚙️ 模型設定")
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
st.markdown("輸入一段文字，讓 AI 為你創作圖片。**(🚀 採用前端直連技術，100% 免疫雲端斷網)**")

with st.container(border=True):
    prompt = st.text_area(
        "請輸入提示詞 (Prompt):",
        placeholder="A cat walking on the beach...",
        height=150
    )
    
    submit_button = st.button("開始生成", type="primary")

st.info("💡 系統已切換至「前端直連模式」，將透過您的瀏覽器直接連線 Hugging Face，完全避開 Streamlit 伺服器網路故障問題。")

# ==========================================
# 5. 究極生圖核心：純前端 JavaScript 直連 Hugging Face
# ==========================================
if submit_button:
    if not prompt.strip():
        st.warning("⚠️ 請輸入您想要生成的圖片提示詞 (Prompt)！")
    elif not active_token:
        st.error("⚠️ 系統無可用金鑰，請在左側輸入您的 Hugging Face Token。")
    else:
        st.success("📡 指令已發送！正在透過前端通道直連 Hugging Face API...")
        
        # 將 Python 變數安全地轉換為 JavaScript 格式字串，避免任何引號衝突
        js_prompt = json.dumps(prompt.strip())
        js_token = json.dumps(active_token)
        js_model = json.dumps(selected_model)
        
        # 打造純 HTML/JS 的前端生圖組件
        html_code = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <script src="https://cdn.tailwindcss.com"></script>
        </head>
        <body class="bg-white p-0 m-0">
            <div class="w-full border border-slate-200 rounded-xl overflow-hidden shadow-lg bg-slate-50 relative p-4">
                
                <div class="relative rounded-lg overflow-hidden bg-slate-200 min-h-[450px] flex items-center justify-center">
                    
                    <div id="loading-layer" class="absolute inset-0 flex flex-col items-center justify-center bg-slate-100 z-0">
                        <svg class="w-12 h-12 text-blue-500 mb-4 animate-spin" fill="none" viewBox="0 0 24 24">
                            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        <p id="status-text" class="text-sm font-bold text-blue-700 animate-pulse">🚀 正在透過瀏覽器直連 Hugging Face...</p>
                        <p id="sub-status" class="text-xs font-medium text-slate-500 mt-2">完全繞過 Streamlit 雲端機房</p>
                    </div>
                    
                    <img id="result-image" src="" class="w-full h-auto max-h-[600px] object-contain relative z-10 shadow-inner opacity-0 transition-opacity duration-700 rounded-lg" alt="AI Image" />
                </div>
                
                <div class="mt-4 p-3 bg-white border border-slate-100 rounded-lg shadow-inner flex flex-col gap-2">
                    <p class="text-xs text-slate-600 font-medium">✨ <strong class="text-slate-800">AI 創作標籤：</strong> <span id="prompt-display"></span></p>
                    <div class="flex items-center gap-2">
                        <span class="px-2 py-0.5 bg-blue-50 border border-blue-200 text-blue-700 rounded text-[10px] font-bold">前端直連通道 (CORS Bypass)</span>
                        <span class="px-2 py-0.5 bg-emerald-50 border border-emerald-200 text-emerald-700 rounded text-[10px] font-bold" id="model-display"></span>
                    </div>
                </div>
            </div>

            <script>
                // 1. 從 Python 安全接收變數
                const promptText = {js_prompt};
                const token = {js_token};
                const model = {js_model};
                const apiUrl = "https://api-inference.huggingface.co/models/" + model;
                
                // 2. 綁定 HTML 元素
                document.getElementById('prompt-display').innerText = promptText;
                document.getElementById('model-display').innerText = model;
                const statusEl = document.getElementById('status-text');
                const subStatusEl = document.getElementById('sub-status');
                const loadingLayer = document.getElementById('loading-layer');
                const imgEl = document.getElementById('result-image');

                // 3. 執行前端非同步 API 呼叫 (自帶 503 喚醒重試機制)
                async function fetchImage() {{
                    try {{
                        let response = await fetch(apiUrl, {{
                            method: 'POST',
                            headers: {{
                                'Authorization': 'Bearer ' + token,
                                'Content-Type': 'application/json'
                            }},
                            body: JSON.stringify({{inputs: promptText}})
                        }});

                        if (response.status === 503) {{
                            const data = await response.json();
                            const waitTime = Math.max(Math.round(data.estimated_time || 20), 1);
                            statusEl.innerText = "⏳ 遠端 AI 模型正在從休眠中喚醒...";
                            statusEl.className = "text-sm font-bold text-amber-600 animate-pulse";
                            subStatusEl.innerText = "預計需要等待 " + waitTime + " 秒，系統將自動為您重試...";
                            
                            // 設定計時器自動重試
                            setTimeout(fetchImage, Math.min(waitTime * 1000, 15000));
                            return;
                        }}

                        if (!response.ok) {{
                            const errText = await response.text();
                            statusEl.innerText = "❌ 發生連線錯誤";
                            statusEl.className = "text-sm font-bold text-red-600";
                            subStatusEl.innerText = "狀態碼: " + response.status + " | 訊息: " + errText;
                            return;
                        }}

                        // 成功取得圖片！
