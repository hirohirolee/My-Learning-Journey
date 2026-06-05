import streamlit as st
import streamlit.components.v1 as components
import urllib.parse
import random
import time
import requests
import io
from PIL import Image

# ==========================================
# 1. 網頁基本設定
# ==========================================
st.set_page_config(
    page_title="AI 圖像生成 Web App",
    page_icon="🎨",
    layout="wide"
)

# ==========================================
# 2. 安全地讀取系統預設 API Key
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
            st.error("❌ 當前連線狀態：無可用憑證，將使用備用通道出圖")

    st.divider()
    st.markdown("### ⚙️ 模型設定")
    selected_model = st.selectbox(
        "選擇 AI 模型:",
        (
            "black-forest-labs/FLUX.1-schnell",
            "stabilityai/sdxl-turbo",
            "stabilityai/stable-diffusion-xl-base-1.0",
            "nvidia/Cosmos3-Super-Text2Image"
        )
    )

# ==========================================
# 4. 主畫面設計
# ==========================================
st.title("🎨 AI 圖像生成 Web App")
st.markdown("輸入一段文字，讓 AI 為你創作圖片。**(支援金鑰自訂，免填則自動啟用託管憑證)**")

with st.container(border=True):
    prompt = st.text_area(
        "請輸入提示詞 (Prompt):",
        placeholder="An astronaut riding a horse on mars, hd, dramatic lighting",
        height=150
    )
    
    submit_button = st.button("開始生成", type="primary")

st.info("💡 提示：Hugging Face 免費模型若處於休眠狀態，首次連線喚醒可能需要 20~60 秒，系統將為您自動重試。")

# ==========================================
# 5. 生成核心邏輯 (Hugging Face 智能重試喚醒機制)
# ==========================================
if submit_button:
    if not prompt.strip():
        st.warning("⚠️ 請輸入您想要生成的圖片提示詞 (Prompt)！")
    else:
        trigger_fallback = False
        
        # 優先使用 Hugging Face
        if active_token:
            with st.spinner(f"🚀 正在連線 Hugging Face [{selected_model}]... (若遇模型休眠，請耐心等候)"):
                API_URL = f"https://api-inference.huggingface.co/models/{selected_model}"
                headers = {"Authorization": f"Bearer {active_token}"}
                payload = {"inputs": prompt.strip()}
                
                max_retries = 5  # 最多嘗試 5 次喚醒
                success = False
                
                for attempt in range(max_retries):
                    try:
                        # 將超時時間大幅拉長至 60 秒，給模型足夠的時間繪圖
                        response = requests.post(API_URL, headers=headers, json=payload, timeout=60)
                        
                        if response.status_code == 200:
                            # 成功出圖！
                            image_bytes = response.content
                            image = Image.open(io.BytesIO(image_bytes))
                            st.success("🎉 [主通道成功] Hugging Face 官方 API 圖片生成完畢！")
                            st.image(image, caption=prompt.strip(), use_container_width=True)
                            success = True
                            break
                            
                        elif response.status_code == 503:
                            # 遇到 503 代表模型正在睡覺，提取需要等待的秒數
                            error_data = response.json()
                            wait_time = error_data.get("estimated_time", 20)
                            
                            # 在畫面上發出提示，讓你知道系統正在努力
                            st.toast(f"⏳ 遠端模型喚醒中... 預計需 {wait_time:.1f} 秒，系統自動重試中 ({attempt+1}/{max_retries})")
                            
                            # 暫停執行並等待模型載入
                            time.sleep(min(wait_time, 20))
                            
                        else:
                            # 其他嚴重錯誤 (如 Token 權限不足、請求格式錯誤)
                            st.error(f"❌ Hugging Face 發生錯誤 (狀態碼: {response.status_code}): {response.text}")
                            trigger_fallback = True
                            break
                            
                    except requests.exceptions.Timeout:
                        st.toast(f"⚠️ 連線超時，正在重新嘗試 ({attempt+1}/{max_retries})...")
                    except requests.exceptions.ConnectionError:
                        st.error("❌ 嚴重錯誤：Streamlit 雲端伺服器對外網路中斷 (NameResolutionError)！")
                        trigger_fallback = True
                        break
                    except Exception as e:
                        st.error(f"❌ 發生未知的連線錯誤: {e}")
                        trigger_fallback = True
                        break
                
                # 如果重試了 5 次都失敗，再切換到備用通道
                if not success and not trigger_fallback:
                    st.warning("⚠️ Hugging Face 伺服器滿載或喚醒失敗，正在自動切換至備用通道...")
                    trigger_fallback = True
        else:
            trigger_fallback = True

        # ==========================================
        # 通道二：備用免 Key 閃電生圖通道 (安全保底)
        # ==========================================
        if trigger_fallback:
            st.warning("📡 遠端主通道無法連線，已自動為您切換至【備用免 Key 閃電生圖通道】！")
            
            encoded_prompt = urllib.parse.quote(prompt.strip().replace('\n', ' '))
            random_seed = random.randint(1, 99999)
            target_image_url = f"https://image.pollinations.ai/p/{encoded_prompt}?width=800&height=600&model=turbo&seed={random_seed}"
            
            html_lines = [
                "<!DOCTYPE html>",
                "<html>",
                "<head>",
                "    <meta charset='UTF-8'>",
                "    <script src='https://cdn.tailwindcss.com'></script>",
                "    <style>",
                "        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: .4; } }",
                "        .animate-pulse { animation: pulse 1.5s cubic-bezier(0.4, 0, 0.6, 1) infinite; }",
                "    </style>",
                "</head>",
                "<body class='bg-white p-0 m-0 flex flex-col items-center justify-center'>",
                "    <div class='w-full border border-slate-200 rounded-xl overflow-hidden shadow-lg bg-slate-50 relative p-4'>",
                "        <div class='relative rounded-lg overflow-hidden bg-slate-200 min-h-[450px] flex items-center justify-center'>",
                "            <div id='skeleton' class='absolute inset-0 flex flex-col items-center justify-center bg-slate-100 text-slate-400 animate-pulse z-0'>",
                "                <p class='text-xs font-semibold'>🚀 閃電通道即時渲染中，請稍候 2~3 秒...</p>",
                "            </div>",
                "            <img src='" + target_image_url + "' class='w-full h-auto max-h-[600px] object-contain relative z-10 shadow-inner opacity-0 transition-opacity duration-300 rounded-lg' onload=\"document.getElementById('skeleton').style.display='none'; this.classList.remove('opacity-0');\" alt='AI Generated Image' />",
                "        </div>",
                "        <div class='mt-4 p-3 bg-white border border-slate-100 rounded-lg shadow-inner'>",
                "            <p class='text-xs text-slate-500 font-medium'>✨ <strong>AI 創作標籤：</strong> " + prompt.strip() + "</p>",
                "            <div class='flex items-center gap-2 mt-2'>",
                "                <span class='px-2 py-0.5 bg-indigo-50 border border-indigo-100 text-indigo-600 rounded text-[10px] font-bold'>Turbo 極速通道</span>",
                "                <span class='px-2 py-0.5 bg-emerald-50 border border-emerald-100 text-emerald-600 rounded text-[10px] font-bold'>密鑰安全託管中</span>",
                "                <a href='" + target_image_url + "' target='_blank' class='text-[11px] text-blue-600 hover:underline font-semibold ml-auto'>🔗 點此查看高清原圖</a>",
                "            </div>",
                "        </div>",
                "    </div>",
                "</body>",
                "</html>"
            ]
            
            html_code = "\n".join(html_lines)
            components.html(html_code, height=580, scrolling=False)
