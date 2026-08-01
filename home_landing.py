import streamlit as st

# Custom Styling with modern aesthetic
st.markdown("""
    <style>
    .main-title {
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, #1E88E5 0%, #7B1FA2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .sub-title {
        font-size: 1.15rem;
        color: #888888;
        margin-bottom: 2rem;
    }
    .category-box {
        background-color: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 1.2rem;
        margin-bottom: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">🚀 My Learning Journey | 全方位專案作品集</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">歡迎來到我的 AI 數據、ESG 永續、量化選股與多元應用展示平台。請使用左側選單或「🔽 下拉快速選單」切換專案！</div>', unsafe_allow_html=True)

st.divider()

# Overview Statistics / Metrics
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric(label="專案類別", value="5 大分類", delta="完整架構")
with col2:
    st.metric(label="展示頁面", value="28 個功能頁", delta="全數 0 錯誤")
with col3:
    st.metric(label="技術堆疊", value="Python / ML / AI", delta="Streamlit Native")
with col4:
    st.metric(label="導覽體驗", value="下拉選單 + 自動換列", delta="全字體無遮擋")

st.markdown("### 🌟 5 大主題專案地圖")

c1, c2 = st.columns(2)

with c1:
    st.markdown("""
    <div class="category-box">
    <h4>🤖 1. AI 與數據機器學習專案 (Daily Lessons)</h4>
    包含 Top 10 機器學習模型演算法、波士頓/加州房價回歸預測、3D SVM 核技巧視覺化、Puter.js AI 圖像生成、影視劇迷分析器與 CWA 氣象 AI 預報。
    </div>
    
    <div class="category-box">
    <h4>🌿 2. ESG 企業永續專案 (ESG Sustainability)</h4>
    符合 GRI 準則與 ISO 14064-1 溫室氣體盤查規範，包含 ESG 企業永續報告生成系統與動態重大性門檻矩陣。
    </div>
    
    <div class="category-box">
    <h4>📈 3. 台灣 AI 量化選股系統 (Quant Stock System)</h4>
    完整整合 AI 每日選股秘笈 (挑蘋果秘笈)、量化策略回測時光機、新聞與討論區阿姨八卦風向、以及 AI 模型預測成績單 (誠實豆沙包)。
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown("""
    <div class="category-box">
    <h4>🛡️ 4. 數位韌性與大數據應用 (Digital Resilience & Data)</h4>
    包含數位韌性監控儀表板、製造業 AI 決策系統、BTC/ETH 區塊鏈分析儀表板、樂透大數據分析、跨論壇討論區爬蟲與體育賽事數據分析。
    </div>
    
    <div class="category-box">
    <h4>🎮 5. 生活趣味與遊戲專案 (Misc & Mini Games)</h4>
    包含大白話易經卦象占卜、圖像馬賽克與防護處理、皇家遊戲對決工具，以及 21點 (Blackjack)、小精靈迷宮 (Pacman) 與井字棋 (Tic-Tac-Toe)。
    </div>
    """, unsafe_allow_html=True)
