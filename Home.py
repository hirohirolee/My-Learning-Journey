import sys
import os
import streamlit as st

# 1. Set top-level page config ONCE at the start of Home.py
st.set_page_config(
    page_title="My Learning Journey",
    page_icon="🚀",
    layout="wide"
)

# 2. Safely prevent sub-pages from raising StreamlitAPIException when calling st.set_page_config
_original_set_page_config = st.set_page_config
def _safe_set_page_config(*args, **kwargs):
    pass

st.set_page_config = _safe_set_page_config

# Automatically append sub-app directories to sys.path so sub-app internal imports work seamlessly
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CANDIDATE_ROOT = os.path.join(BASE_DIR, "streamlit_candidates")

candidate_paths = [
    os.path.join(CANDIDATE_ROOT, "02_ESG_Sustainability", "ESG_Reporting_System"),
    os.path.join(CANDIDATE_ROOT, "04_Misc_Applications", "finance", "tw_ai_quant_system", "web_ui"),
    os.path.join(CANDIDATE_ROOT, "04_Misc_Applications", "finance", "tw_ai_quant_system"),
    os.path.join(CANDIDATE_ROOT, "04_Misc_Applications", "lotto"),
    os.path.join(CANDIDATE_ROOT, "04_Misc_Applications", "Digital_Resilience_Dashboard", "app"),
    os.path.join(CANDIDATE_ROOT, "04_Misc_Applications", "CHING_YiJing"),
    os.path.join(CANDIDATE_ROOT, "04_Misc_Applications", "BTCETH"),
]

for p in candidate_paths:
    if os.path.exists(p) and p not in sys.path:
        sys.path.insert(0, p)

# Define Streamlit Pages with explicit URL url_path to ensure uniqueness
home_page = st.Page(
    "home_landing.py",
    title="首頁總覽",
    icon="🏠",
    url_path="home",
    default=True
)

esg_page = st.Page(
    "streamlit_candidates/02_ESG_Sustainability/ESG_Reporting_System/esgreport.py",
    title="ESG 企業永續報告生成系統",
    icon="🌱",
    url_path="esg-reporting"
)

quant_page = st.Page(
    "streamlit_candidates/04_Misc_Applications/finance/tw_ai_quant_system/web_ui/app.py",
    title="台灣 AI 量化選股系統",
    icon="📊",
    url_path="tw-quant-system"
)

lotto_page = st.Page(
    "streamlit_candidates/04_Misc_Applications/lotto/app.py",
    title="樂透大數據分析器",
    icon="🎰",
    url_path="lotto-analyzer"
)

resilience_page = st.Page(
    "streamlit_candidates/04_Misc_Applications/Digital_Resilience_Dashboard/app/app.py",
    title="數位韌性監控儀表板",
    icon="🛡️",
    url_path="digital-resilience"
)

yijing_page = st.Page(
    "streamlit_candidates/04_Misc_Applications/CHING_YiJing/app.py",
    title="易經卦象占卜應用",
    icon="🔮",
    url_path="yijing-divination"
)

btceth_page = st.Page(
    "streamlit_candidates/04_Misc_Applications/BTCETH/app.py",
    title="BTC/ETH 區塊鏈儀表板",
    icon="🪙",
    url_path="btc-eth-dashboard"
)

# Organize pages into navigation sections
pg = st.navigation(
    {
        "主頁總覽": [home_page],
        "核心系統 (Core Systems)": [esg_page, quant_page],
        "數據與分析工具": [lotto_page, resilience_page, btceth_page],
        "生活與文化應用": [yijing_page],
    }
)

# Run Navigation
pg.run()
