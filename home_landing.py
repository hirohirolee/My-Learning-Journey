import streamlit as st

# Custom Styling with modern aesthetic
st.markdown("""
    <style>
    .main-title {
        font-size: 2.6rem;
        font-weight: 800;
        background: linear-gradient(135deg, #1E88E5 0%, #7B1FA2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .sub-title {
        font-size: 1.2rem;
        color: #555555;
        margin-bottom: 2rem;
    }
    .card {
        background-color: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(200, 200, 200, 0.2);
        border-radius: 12px;
        padding: 1.2rem;
        margin-bottom: 1rem;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">🚀 My Learning Journey & Project Portfolio</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">歡迎來到我的 AI、數據分析與永續 ESG 實作展示平台。透過左側選單可切換不同精選專案！</div>', unsafe_allow_html=True)

st.divider()

# Overview Statistics / Metrics
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric(label="專案領域", value="4 大領域", delta="AI / ESG / Quant / Tools")
with col2:
    st.metric(label="精選應用", value="6+ 個", delta="雙核心系統")
with col3:
    st.metric(label="開發語言", value="Python 3.11+", delta="Streamlit Ecosystem")
with col4:
    st.metric(label="部署狀態", value="Streamlit Cloud", delta="Ready")

st.markdown("### 🌟 精選專案導覽")

col_left, col_right = st.columns(2)

with col_left:
    st.markdown("""
    ### 🌱 ESG 企業永續與報告書
    - **ESG 企業永續報告生成系統**
      符合 GRI 準則與 ISO 14064-1 溫室氣體盤查規範，自動化產出企業 ESG 永續報告與統計分析。
    
    ### 📊 金融科技與 AI 量化選股
    - **台灣 AI 量化選股系統**
      整合技術指標、籌碼面、新聞情緒分析與 AI 策略掃描，提供多面向的台股投資決策支援。
    
    ### 🪙 加密貨幣儀表板
    - **BTC / ETH 數據監控**
      即時鏈上與市場數據分析儀表板。
    """)

with col_right:
    st.markdown("""
    ### 🎰 實用大數據工具
    - **樂透大數據分析器**
      對歷史中獎數據進行冷熱號碼分析、機率分布推算與號碼推薦。
    
    ### 🛡️ 數位韌性監控
    - **數位韌性儀表板**
      監控系統韌性指標與風險預警機制。
    
    ### ☯️ 傳統智慧應用
    - **易經卦象占卜應用**
      將傳統易經數理融入互動式占卜決策輔助工具。
    """)

st.divider()
st.info("💡 **使用提示**：請點擊左側邊欄選單切換至各專案系統體驗完整功能。")
