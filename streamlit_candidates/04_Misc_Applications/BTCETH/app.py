import streamlit as st
from config import settings
from utils.logger import configure_logger
from utils.formatter import format_currency, format_duration
from core.bitcoin_api import bitcoin_api
from ui.metrics import inject_custom_css
from ui.sidebar import render_sidebar
from ui.dashboard import render_dashboard
from loguru import logger
import time

def main() -> None:
    """Main application entry point.
    
    Sets up the Streamlit page layout, initializes configurations,
    fetches live blockchain data, and renders the user interface.
    """
    # 1. Page Configuration
    st.set_page_config(
        page_title="比特幣單機挖礦分析平台",
        page_icon="🪙",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # 2. Configure Logging
    # Check if we are running in debug mode (can be passed via query params or session state)
    is_debug = st.sidebar.toggle("啟用偵錯日誌", value=False)
    configure_logger(debug=is_debug)
    logger.info("Streamlit application initialized.")

    # 3. Inject CSS
    inject_custom_css()

    # 4. Fetch Live Data with Force Refresh option
    st.sidebar.markdown("### 數據同步")
    force_refresh = st.sidebar.button(
        "同步最新網路數據", 
        help="強制應用程式拉取最新的價格和難度指標。"
    )
    
    if force_refresh:
        st.cache_data.clear()  # Clear Streamlit cache if manual sync is triggered
        logger.info("Manual refresh triggered. Clearing Streamlit cache.")
        
    with st.spinner("正在獲取最新區塊鏈數據..."):
        try:
            live_data = bitcoin_api.get_blockchain_data(force_refresh=force_refresh)
            logger.info("Successfully fetched network data.")
        except Exception as e:
            logger.critical(f"Critical failure while fetching network data: {e}")
            st.error("無法獲取網路數據。正使用硬編碼設定。")
            # Emergency fallback structure if the API manager completely errors out
            live_data = bitcoin_api._get_hardcoded_fallback()
            live_data["timestamp"] = time.time()
            live_data["halving_countdown_blocks"] = 0
            live_data["halving_countdown_time_secs"] = 0.0

    # Show last sync timestamp in sidebar
    last_sync_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(live_data["timestamp"]))
    st.sidebar.caption(f"最後更新時間: {last_sync_time}")

    # 5. Render Sidebar Controls
    user_settings = render_sidebar(live_data)

    # 6. Main Dashboard Render
    st.title("🪙 比特幣單機挖礦分析平台")
    st.caption("評估「彩票挖礦」(單機挖礦)的數學可行性、財務回報以及模擬模型。")
    st.markdown("---")

    # Render actual analysis tabs and visualizations
    render_dashboard(user_settings, live_data)

    # 7. Page Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #64748b; font-size: 0.8rem;'>"
        "比特幣單機挖礦分析平台 • 專為生產級投資組合評估開發"
        "</div>",
        unsafe_allow_html=True
    )

main()
