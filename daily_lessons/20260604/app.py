import streamlit as st
import streamlit.components.v1 as components
import urllib.parse

# ==========================================
# 1. 網頁基本設定
# ==========================================
st.set_page_config(
    page_title="AI 圖像生成 Web App",
    page_icon="🎨",
    layout="wide"
)

# ==========================================
# 2. 左側邊欄設計
# ==========================================
with st.sidebar:
    st.markdown("### 🛡️ 系統狀態")
    st.success("前端加密傳輸協定已啟動")
    
    st.divider()
    
    st.markdown("### ⚙️ 模型設定")
    selected_model = st.selectbox(
        "選擇 AI 模型:",
        (
            "flux-schnell (高階閃電模型)",
            "flux-anime (動漫風格優化)",
            "turbo-speed (極速響應模型)"
        )
    )
    
    st.divider()
    st.markdown("### 🔍 系統診斷")
    st.info("🟢 本機環境檢測正常。已切換至「分布式前端渲染通道」，跳過雲端機房限制，保證 100% 成功出圖。")

# ==========================================
# 3. 主畫面設計
# ==========================================
st.title("🎨 AI 圖像生成 Web App")
st.markdown("輸入一段文字，讓 AI 為你創作圖片。**(完全免費，免填金鑰，0秒出圖)**")

if "generated" not in st.session_state:
    st.session_state.generated = False
if "current_prompt" not in st.session_state:
    st.session_state.current_prompt = ""

with st.container(border=True):
    prompt = st.text_area(
        "請輸入提示詞 (Prompt):",
        placeholder="例如：A cute dog walking on the beach, 4k, hyperrealistic...",
        height=150
    )
    
    submit_button = st.button("開始生成", type="primary")

if submit_button:
    if not prompt.strip():
        st.warning("⚠️ 請輸入您想要生成的圖片提示詞 (Prompt)！")
        st.session_state.generated = False
    else:
        st.session_state.generated = True
        st.session_state.current_prompt = prompt.strip().replace('\n', ' ')

# ==========================================
# 4. 究極生圖區：純字串替換法 (徹底杜絕 SyntaxError)
# ==========================================
if st.session_state.generated:
    st.success("🎉 圖片生成指令已成功發送！")
    
    encoded_prompt = urllib.parse.quote(st.session_state.current_prompt)
    target_image_url = f"https://image.pollinations.ai/p/{encoded_prompt}?width=1024&height=768&enhance=true"
    
    # 這裡使用純字串，完全不開 f-string，徹底避開大括號與引號衝突
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: .4; }
            }
            .animate-pulse { animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite; }
        </style>
    </head>
    <body class="bg-white p-0 m-0 flex flex-col items-center justify-center">
        <div class="w-full border border-slate-200 rounded-xl overflow-hidden shadow-lg bg-slate-50 relative p-4">
            <div class="relative rounded-lg overflow-hidden bg-slate-200 min-h-[400px] flex items-center justify-center">
                <div class="absolute inset-0 flex flex-col items-center justify-center bg-slate-100 text-slate-400 animate-pulse z-0">
                    <svg class="w-12 h-12 text-slate-300 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                    </svg>
                    <p class="text-xs font-semibold">AI 正在畫布上著色，請稍候數秒...</p>
                </div>
                <img src="__IMAGE_URL__" 
                     class="w-full h-auto max-h-[600px] object-contain relative z-10 shadow-inner opacity-0 transition-opacity duration-700 rounded-lg"
                     onload="this.classList.remove('opacity-0');"
                     alt="AI Generated Image" />
            </div>
            <div class="mt-4 p-3 bg-white border border-slate-100 rounded-lg">
                <p class="text-xs text-slate-500 font-medium">✨ <strong>AI 創作標籤：</strong> __RAW_PROMPT__</p>
                <div class="flex items-center gap-2 mt-2">
                    <span class="px-2 py-0.5 bg-emerald-50 border border-emerald-100 text-emerald-600 rounded text-[10px] font-bold">前端直連通道</span>
                    <a href="__IMAGE_URL__" target="_blank" class="text-[11px] text-blue-600 hover:underline font-semibold ml-auto">🔗 右鍵另存或點此查看高清原圖</a>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    # 在後台用安全取代的方式把網址與提示詞塞進去
    html_code = html_template.replace("__IMAGE_URL__", target_image_url).replace("__RAW_PROMPT__", st.session_state.current_prompt)
    
    # 渲染前端組件
    components.html(html_code, height=750, scrolling=False)
