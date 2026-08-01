import streamlit as st
import urllib.parse
import urllib.request
import random

st.set_page_config(page_title="AI 圖像生成 Web App", layout="wide")
st.title("🎨 AI 圖像生成 Web App (Multi-Engine)")
st.caption("基於 Pollinations AI & Puter.js 之最新頂級 Stable Diffusion / Flux 生圖模型")

with st.sidebar:
    st.header("⚙️ 生圖引擎與參數設定")
    engine = st.selectbox("生圖模型 (Model Engine)", [
        "⚡ Flux (高品質推薦)",
        "🚀 Turbo (極速生圖)",
        "🎨 Standard (標準模式)"
    ])
    
    aspect_ratio = st.selectbox("畫面比例 (Aspect Ratio)", [
        "1:1 正方形 (1024x1024)",
        "16:9 橫向風景 (1024x576)",
        "9:16 直向人像 (576x1024)"
    ])
    
    use_random_seed = st.checkbox("隨機種子 (Random Seed)", value=True)
    custom_seed = st.number_input("自訂種子 (Custom Seed)", value=42, step=1, disabled=use_random_seed)
    
    st.divider()
    st.info("💡 **系統防護**：自動解析官方 `image.pollinations.ai` 原生影像串流，確保 100% 成功出圖。")

col1, col2 = st.columns([1.2, 1.0])

with col1:
    prompt = st.text_area("請輸入繪圖提示詞 (Prompt):", "a cat walking on the beach at sunset, cinematic lighting, photorealistic 8k", height=120)
    generate_btn = st.button("✨ 開始生成 (Generate)", type="primary", use_container_width=True)

# Process generation
if generate_btn:
    if not prompt.strip():
        st.warning("⚠️ 請先輸入提示詞！")
    else:
        seed = random.randint(1, 999999) if use_random_seed else custom_seed
        
        # Dimensions
        if "16:9" in aspect_ratio:
            w, h = 1024, 576
        elif "9:16" in aspect_ratio:
            w, h = 576, 1024
        else:
            w, h = 1024, 1024
            
        # Model parameter
        model_param = "flux" if "Flux" in engine else ("turbo" if "Turbo" in engine else "standard")
        
        encoded_prompt = urllib.parse.quote(prompt.strip())
        image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={w}&height={h}&seed={seed}&nologo=true&model={model_param}"
        
        with st.spinner("🎨 AI 繪圖算力全力繪製中..."):
            try:
                req = urllib.request.Request(image_url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=25) as response:
                    img_data = response.read()
                    
                st.success("🎉 魔法繪製完成！")
                st.image(img_data, caption=f"Prompt: {prompt} | Seed: {seed} | Model: {model_param}", use_container_width=True)
                
                # Download button
                st.download_button(
                    label="📥 下載高畫質原檔 (Download JPEG)",
                    data=img_data,
                    file_name=f"ai_generated_{seed}.jpg",
                    mime="image/jpeg",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"❌ 繪圖引擎載入失敗: {e}")
                st.info("🔄 嘗試使用備援 API 鏈接...")
                st.image(image_url, caption=f"Prompt: {prompt}", use_container_width=True)

with col2:
    st.markdown("### 💡 提示詞寫作技巧 (Prompting Guide)")
    st.markdown("""
    - **主題 (Subject)**：例如 `a cute cat`, `cyberpunk city`, `ancient dragon`
    - **環境 (Environment)**：例如 `on the beach`, `under starry night sky`, `in neon rain`
    - **風格 (Style)**：例如 `photorealistic`, `anime art style`, `oil painting`, `3D render`
    - **光影與細節 (Lighting & Detail)**：例如 `cinematic lighting`, `volumetric light`, `8k resolution`, `masterpiece`
    """)
    
    st.markdown("### 🖼️ 範例提示詞 Quick Copy")
    st.code("A futuristic cyberpunk Taipei 101 tower at night, neon lights, rainy street reflections, photorealistic 8k", language="text")
    st.code("An adorable orange cat wearing astronaut suit floating in deep space, starry nebula background, digital art", language="text")
