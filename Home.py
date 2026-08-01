import sys
import os
import streamlit as st

# 1. Set top-level page config ONCE at the start of Home.py
st.set_page_config(
    page_title="My Learning Journey | Full Portfolio",
    page_icon="🚀",
    layout="wide"
)

# 2. Safely prevent sub-pages from raising StreamlitAPIException when calling st.set_page_config
_original_set_page_config = st.set_page_config
def _safe_set_page_config(*args, **kwargs):
    pass

st.set_page_config = _safe_set_page_config

# 3. Automatically append candidate directories to sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CANDIDATE_ROOT = os.path.join(BASE_DIR, "streamlit_candidates")

candidate_paths = [
    # Category 1
    os.path.join(CANDIDATE_ROOT, "01_AI_Data_Projects", "daily_lessons", "20260604"),
    os.path.join(CANDIDATE_ROOT, "01_AI_Data_Projects", "daily_lessons", "20260605"),
    os.path.join(CANDIDATE_ROOT, "01_AI_Data_Projects", "daily_lessons", "20260608"),
    os.path.join(CANDIDATE_ROOT, "01_AI_Data_Projects", "daily_lessons", "20260609"),
    os.path.join(CANDIDATE_ROOT, "01_AI_Data_Projects", "daily_lessons", "20260615"),
    os.path.join(CANDIDATE_ROOT, "01_AI_Data_Projects", "daily_lessons", "20260618"),
    os.path.join(CANDIDATE_ROOT, "01_AI_Data_Projects", "daily_lessons", "20260630"),
    os.path.join(CANDIDATE_ROOT, "01_AI_Data_Projects", "daily_lessons", "20260702"),
    # Category 2
    os.path.join(CANDIDATE_ROOT, "02_ESG_Sustainability", "ESG_Reporting_System"),
    # Category 3
    os.path.join(CANDIDATE_ROOT, "04_Misc_Applications", "finance", "tw_ai_quant_system", "web_ui"),
    os.path.join(CANDIDATE_ROOT, "04_Misc_Applications", "finance", "tw_ai_quant_system"),
    os.path.join(CANDIDATE_ROOT, "04_Misc_Applications", "lotto"),
    os.path.join(CANDIDATE_ROOT, "04_Misc_Applications", "Digital_Resilience_Dashboard", "app"),
    os.path.join(CANDIDATE_ROOT, "04_Misc_Applications", "Digital_Resilience_Dashboard"),
    os.path.join(CANDIDATE_ROOT, "04_Misc_Applications", "CHING_YiJing"),
    os.path.join(CANDIDATE_ROOT, "04_Misc_Applications", "BTCETH"),
    os.path.join(CANDIDATE_ROOT, "04_Misc_Applications", "crawler_dis", "ui"),
    os.path.join(CANDIDATE_ROOT, "04_Misc_Applications", "crawler_dis"),
    os.path.join(CANDIDATE_ROOT, "04_Misc_Applications", "Sports Analysis"),
    os.path.join(CANDIDATE_ROOT, "04_Misc_Applications", "Royalgame"),
    os.path.join(CANDIDATE_ROOT, "04_Misc_Applications", "Mosaic"),
    os.path.join(CANDIDATE_ROOT, "04_Misc_Applications", "15games"),
]

for p in candidate_paths:
    if os.path.exists(p) and p not in sys.path:
        sys.path.insert(0, p)

# =====================================================================
# Page Declarations
# =====================================================================

# 1. Home
home_page = st.Page("home_landing.py", title="首頁總覽", icon="🏠", url_path="home", default=True)

# 2. AI & Data Projects (daily_lessons)
ai_t2i = st.Page("streamlit_candidates/01_AI_Data_Projects/daily_lessons/20260604/texttoimage.py", title="AI 圖像生成 (Text2Image)", icon="🎨", url_path="ai-text2image")
ai_linear = st.Page("streamlit_candidates/01_AI_Data_Projects/daily_lessons/20260605/linear.py", title="線性回歸擬合展示", icon="📈", url_path="ai-linear-regression")
ai_top10 = st.Page("streamlit_candidates/01_AI_Data_Projects/daily_lessons/20260608/top10ml.py", title="Top 10 機器學習模型", icon="🤖", url_path="ai-top10-ml")
ai_startup = st.Page("streamlit_candidates/01_AI_Data_Projects/daily_lessons/20260609/50startup.py", title="50 Startup 商業預測", icon="🏢", url_path="ai-50startups")
ai_boston = st.Page("streamlit_candidates/01_AI_Data_Projects/daily_lessons/20260615/boston_app.py", title="波士頓房價預測", icon="🏠", url_path="ai-boston-housing")
ai_california = st.Page("streamlit_candidates/01_AI_Data_Projects/daily_lessons/20260615/california_app.py", title="加州房價預測", icon="🌴", url_path="ai-california-housing")
ai_svm = st.Page("streamlit_candidates/01_AI_Data_Projects/daily_lessons/20260618/SVM_app.py", title="3D SVM 核技巧視覺化", icon="🔮", url_path="ai-3d-svm")
ai_drama = st.Page("streamlit_candidates/01_AI_Data_Projects/daily_lessons/20260630/app.py", title="影視劇迷分析器", icon="🎬", url_path="ai-drama-analyzer")
ai_weather = st.Page("streamlit_candidates/01_AI_Data_Projects/daily_lessons/20260702/app.py", title="CWA 氣象與 AI 預報", icon="☀️", url_path="ai-cwa-weather")

# 3. ESG Sustainability
esg_main = st.Page("streamlit_candidates/02_ESG_Sustainability/ESG_Reporting_System/esgreport.py", title="ESG 企業永續報告生成系統", icon="🌱", url_path="esg-reporting-system")
esg_legacy = st.Page("streamlit_candidates/02_ESG_Sustainability/ESG_Reporting_System/app_legacy.py", title="ESG 重大性矩陣 (Legacy)", icon="☘️", url_path="esg-materiality-matrix")

# 4. Misc Applications
quant_main = st.Page("streamlit_candidates/04_Misc_Applications/finance/tw_ai_quant_system/web_ui/app.py", title="台灣 AI 量化選股系統", icon="📊", url_path="tw-ai-quant-main")
quant_apple = st.Page("streamlit_candidates/04_Misc_Applications/finance/tw_ai_quant_system/web_ui/pages/01_🔥_阿嬤的每日挑蘋果秘笈.py", title="AI 每日選股秘笈", icon="🍎", url_path="tw-ai-quant-apple")
quant_time = st.Page("streamlit_candidates/04_Misc_Applications/finance/tw_ai_quant_system/web_ui/pages/02_📊_阿嬤的時光機.py", title="量化策略回測時光機", icon="⏰", url_path="tw-ai-quant-time-machine")
quant_gossip = st.Page("streamlit_candidates/04_Misc_Applications/finance/tw_ai_quant_system/web_ui/pages/03_📰_市場阿姨們的八卦風向.py", title="新聞與討論區情緒風向", icon="📰", url_path="tw-ai-quant-gossip")
quant_eval = st.Page("streamlit_candidates/04_Misc_Applications/finance/tw_ai_quant_system/web_ui/pages/05_🎯_老頭家誠實豆沙包.py", title="AI 模型預測成績單", icon="🎯", url_path="tw-ai-quant-eval")

lotto_app = st.Page("streamlit_candidates/04_Misc_Applications/lotto/app.py", title="樂透大數據分析器", icon="🎰", url_path="lotto-analyzer")
resilience_main = st.Page("streamlit_candidates/04_Misc_Applications/Digital_Resilience_Dashboard/app/app.py", title="數位韌性監控儀表板", icon="🛡️", url_path="digital-resilience-main")
resilience_legacy = st.Page("streamlit_candidates/04_Misc_Applications/Digital_Resilience_Dashboard/app_legacy.py", title="製造業 AI 決策系統 (Legacy)", icon="⚙️", url_path="digital-resilience-legacy")
yijing_app = st.Page("streamlit_candidates/04_Misc_Applications/CHING_YiJing/app.py", title="大白話易經卦象占卜", icon="🔮", url_path="yijing-divination")
btceth_app = st.Page("streamlit_candidates/04_Misc_Applications/BTCETH/app.py", title="BTC/ETH 區塊鏈分析儀表板", icon="🪙", url_path="btc-eth-analytics")
crawler_app = st.Page("streamlit_candidates/04_Misc_Applications/crawler_dis/ui/app.py", title="跨論壇討論區爬蟲系統", icon="🕷️", url_path="forum-crawler-ui")
sports_app = st.Page("streamlit_candidates/04_Misc_Applications/Sports Analysis/main.py", title="體育賽事數據分析", icon="⚽", url_path="sports-analysis-engine")
royal_app = st.Page("streamlit_candidates/04_Misc_Applications/Royalgame/main.py", title="皇家遊戲輔助工具", icon="👑", url_path="royal-game-tool")
mosaic_app = st.Page("streamlit_candidates/04_Misc_Applications/Mosaic/ImageDe.py", title="圖像馬賽克與防護處理", icon="🖼️", url_path="mosaic-image-de")
game_bj = st.Page("streamlit_candidates/04_Misc_Applications/15games/blackjack.py", title="21 點撲克牌遊戲 (Blackjack)", icon="🃏", url_path="game-blackjack")
game_pacman = st.Page("streamlit_candidates/04_Misc_Applications/15games/pacman.py", title="小精靈迷宮 (Pacman)", icon="👾", url_path="game-pacman")
game_ttt = st.Page("streamlit_candidates/04_Misc_Applications/15games/tictactoe.py", title="井字棋 (Tic-Tac-Toe)", icon="❌", url_path="game-tictactoe")

# Navigation Routing
pg = st.navigation(
    {
        "主頁總覽": [home_page],
        "🤖 AI 與數據學習專案 (AI & Data Projects)": [
            ai_t2i, ai_linear, ai_top10, ai_startup,
            ai_boston, ai_california, ai_svm, ai_drama, ai_weather
        ],
        "🌱 ESG 企業永續專案 (ESG Sustainability)": [
            esg_main, esg_legacy
        ],
        "🛠️ 多元應用系統 (Misc Applications)": [
            quant_main, quant_apple, quant_time, quant_gossip, quant_eval,
            lotto_app, resilience_main, resilience_legacy, yijing_app, btceth_app,
            crawler_app, sports_app, royal_app, mosaic_app,
            game_bj, game_pacman, game_ttt
        ],
    }
)

# Run Navigation
pg.run()
