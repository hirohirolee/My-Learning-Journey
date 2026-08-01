import streamlit as st
import os
import json

st.set_page_config(page_title="高階商務顧問 | 個人品牌網站 (v2 Executive Theme)", page_icon="👔", layout="wide")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "..", "..", "03_Web_Portfolio", "v2_executive_theme"))

def load_file(rel_path):
    full_path = os.path.join(WEB_DIR, rel_path)
    if os.path.exists(full_path):
        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    return ""

# Sidebar settings
with st.sidebar:
    st.header("👔 商務個人網站導覽")
    view_mode = st.radio("選擇展示視圖 (View Mode):", [
        "🌐 原生 HTML5 網站全景展示",
        "📜 專業履歷與 6 大國際認證",
        "💼 核心服務與 STAR 專案實績",
        "🤖 AI Studio 實戰專案展示"
    ])
    
    st.divider()
    st.info("""
    **高階商務顧問主題 (v2 Executive Theme)**
    - 💎 暗色奢華金 (Dark Luxury Gold) 視覺設計
    - 🛡️ PMP 專案管理 & ISO 資安/溫室氣體盤查雙證照
    - ⚡ 響應式 STAR 框架實績展示
    """)

if "🌐" in view_mode:
    st.title("👔 高階商務顧問 | 個人品牌網站")
    st.caption("引領 AI 賦能與永續合規，將國際標準轉化為企業營運優勢。19年經驗企業講師與專案治理專家。")
    
    # Read HTML and CSS/JS
    index_html = load_file("index.html")
    
    css_files = ["css/variables.css", "css/base.css", "css/layout.css", "css/components.css", "css/animations.css"]
    combined_css = "\n".join([load_file(f) for f in css_files])
    
    content_js = load_file("data/content.js")
    app_js = load_file("js/app.js")
    main_js = load_file("js/main.js")
    
    # Embed compiled standalone HTML
    full_html = f"""
    <!DOCTYPE html>
    <html lang="zh-TW">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>高階商務顧問 | AI 與數位轉型</title>
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            {combined_css}
            body {{
                background-color: #0b0f19 !important;
                color: #e2e8f0;
                margin: 0;
                padding: 0;
            }}
            .site-header {{
                position: sticky;
                top: 0;
                z-index: 1000;
            }}
        </style>
    </head>
    <body>
        <!-- Header -->
        <header class="site-header">
            <div class="container" style="display:flex; justify-content:space-between; align-items:center; padding: 1rem 2rem;">
                <a href="#" class="logo" style="font-size:1.4rem; font-weight:700; color:#d97706; text-decoration:none;">
                    EXECUTIVE<span style="color:#38bdf8;">.</span>CONSULTANT
                </a>
                <nav class="nav-links" style="display:flex; gap:1.5rem;">
                    <a href="#profile" style="color:#e2e8f0; text-decoration:none;">首頁簡介</a>
                    <a href="#services" style="color:#e2e8f0; text-decoration:none;">核心服務</a>
                    <a href="#experience" style="color:#e2e8f0; text-decoration:none;">專業經歷</a>
                    <a href="#case-studies" style="color:#e2e8f0; text-decoration:none;">專案實績</a>
                </nav>
            </div>
        </header>

        <main>
            <!-- Hero -->
            <section class="section hero" id="profile" style="padding: 3rem 2rem;">
                <div class="container">
                    <div id="hero-container"></div>
                    <div id="certifications-container" style="margin-top:2rem;"></div>
                </div>
            </section>

            <!-- Experience -->
            <section class="section" id="experience" style="background-color: #111827; padding: 3rem 2rem;">
                <div class="container">
                    <h2 style="color:#f59e0b; border-bottom: 2px solid #f59e0b; padding-bottom: 0.5rem;">專業經歷 (Experience)</h2>
                    <p style="color:#94a3b8;">近 20 年跨國營運與數位轉型實戰，引領企業突破瓶頸、創造指數型成長。</p>
                    <div id="experience-container"></div>
                </div>
            </section>

            <!-- Services -->
            <section class="section" id="services" style="padding: 3rem 2rem;">
                <div class="container">
                    <h2 style="color:#38bdf8; border-bottom: 2px solid #38bdf8; padding-bottom: 0.5rem;">核心服務與專業領域</h2>
                    <p style="color:#94a3b8;">針對現代企業面臨的 AI 轉型、資安風險與 ESG 永續挑戰，提供系統化的解決方案。</p>
                    <div id="services-container"></div>
                </div>
            </section>

            <!-- STAR Case Studies -->
            <section class="section" id="case-studies" style="background-color: #111827; padding: 3rem 2rem;">
                <div class="container">
                    <h2 style="color:#38bdf8; border-bottom: 2px solid #38bdf8; padding-bottom: 0.5rem;">專案實績 (Impact & Case Studies)</h2>
                    <p style="color:#94a3b8;">以 STAR 框架解構大型專案，展現可量化的商業價值與合規成果。</p>
                    <div id="case-studies-container"></div>
                </div>
            </section>
        </main>

        <script>
            {content_js}
            {app_js}
            {main_js}
        </script>
    </body>
    </html>
    """
    
    st.components.v1.html(full_html, height=850, scrolling=True)

elif "📜" in view_mode:
    st.header("📜 高階主管個人簡介與國際權威認證")
    col1, col2 = st.columns([1.2, 1.0])
    
    with col1:
        st.subheader("👤 Hiro Lee")
        st.markdown("##### **Executive Manager & AI Integration Expert**")
        st.markdown("""
        * **資歷經驗**：近 20 年跨國營運、資訊架構與數位轉型實戰經驗。
        * **核心理念**：Strategic Leadership & Innovation. Bridging Strategy, Operations, and Information Technology.
        * **學歷背景**：資訊管理碩士 (MIS Master) & MCSE 微軟系統工程師。
        """)
        
    with col2:
        st.subheader("🏆 國際權威專業認證 (Certifications)")
        certs = [
            "🏅 **PMP** 國際專案管理師 (Project Management Professional)",
            "🛡️ **ISO 27001** 資訊安全管理系統主導稽核員",
            "🌱 **ISO 14064-1** 溫室氣體盤查主導稽核員",
            "📊 **ISO 9001** 品質管理系統主導稽核員",
            "📈 **Microsoft Power BI** 數據分析專業認證",
            "💻 **MCSE / MCP** 微軟認證系統工程師"
        ]
        for cert in certs:
            st.success(cert)

elif "💼" in view_mode:
    st.header("💼 核心服務與 STAR 專案實績")
    
    st.markdown("### 🌟 三大核心顧問服務")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("#### 1. 專案管理與營運策略 (PMP)")
        st.write("在高階幕僚與行政主管歷練中，協助企業擬定發展策略，優化跨部門溝通與 PMP 專案執行。")
    with col2:
        st.markdown("#### 2. 科技審計與數據決策")
        st.write("結合資管碩士與 MCSE 背景，導入 AI 應用與進階數據分析技術，進行深度合規性風險評估。")
    with col3:
        st.markdown("#### 3. ESG 永續與淨零路徑")
        st.write("具備 ISO 14064-1 溫室氣體盤查主導稽核員資格。協助企業落實碳盤查與減碳策略。")
        
    st.divider()
    st.markdown("### 🎯 STAR 框架專案實績案例")
    
    with st.expander("📌 案例一：跨國製造業 AI 智化審計與產能最佳化", expanded=True):
        st.markdown("""
        - **Situation (情境)**: 傳統產線品管依賴人工抽檢，造成每季度高額耗損與溝通時差。
        - **Task (任務)**: 導入邊緣 AI 瑕疵檢測系統，並建立數據即時儀表板。
        - **Action (行動)**: 主導跨部門 PMP 專案，結合電腦視覺與自動化通報流程。
        - **Result (成果)**: 瑕疵檢測準確度提升至 99.4%，每年為企業節省數百萬元不良品成本。
        """)

    with st.expander("📌 案例二：企業級 ISO 27001 資安防禦與零信任架構轉型"):
        st.markdown("""
        - **Situation (情境)**: 因應日益嚴峻的資安威脅與跨國合規需求。
        - **Task (任務)**: 重新構建企業資安防護網，並取得 ISO 27001 認證。
        - **Action (行動)**: 擔任主導稽核員，進行全公司資產盤點、風險評估與零信任身分驗證導入。
        - **Result (成果)**: 零缺失通過 ISO 27001 外部驗證，資安事件應變時間縮短 75%。
        """)

else:
    st.header("🤖 AI Studio 實戰展示")
    st.caption("結合最新 AI 技術與實戰沙盒模組")
    
    st.markdown("""
    - 🎨 **AI Image Generation**：基於 Hugging Face Inference API 的高畫質圖像生成系統。
    - 📈 **Linear Regression Analytics**：自適應線上數據擬合與線性迴歸數據科學沙盒。
    - 🧠 **ML Emotion AI**：臉部表情偵測與學習專注度即時分析系統。
    """)
    st.success("💡 提示：您可使用本站導覽前往各 AI 與數據專案頁面進行互動體驗！")
