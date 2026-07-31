import streamlit as st
from config import ASIC_DATABASE, settings
from core.difficulty import convert_hashrate, HASHRATE_MULTIPLIERS
from typing import Dict, Any

def render_sidebar(live_data: Dict[str, Any]) -> Dict[str, Any]:
    """Renders the Streamlit sidebar inputs and returns a dictionary of configuration options.
    
    Args:
        live_data (Dict[str, Any]): Dictionary of current blockchain metrics.
        
    Returns:
        Dict[str, Any]: Consolidated user settings dictionary.
    """
    st.sidebar.image(
        "https://upload.wikimedia.org/wikipedia/commons/4/46/Bitcoin.svg", 
        width=60
    )
    st.sidebar.title("單機挖礦分析")
    st.sidebar.caption("平台設定與假設參數")
    st.sidebar.markdown("---")

    # 1. MINING HARDWARE CONFIGURATION
    st.sidebar.header("🔌 挖礦硬體")
    
    # ASIC Hardware Selection
    asic_names = list(ASIC_DATABASE.keys()) + ["自定義 / 手動輸入"]
    selected_asic_name = st.sidebar.selectbox(
        "ASIC 預設型號",
        options=asic_names,
        index=1,  # Default to Antminer S21
        help="從數據庫選擇標準 ASIC 礦機型號以自動填寫規格。"
    )

    # Prefill logic based on selection
    if selected_asic_name != "自定義 / 手動輸入":
        specs = ASIC_DATABASE[selected_asic_name]
        default_hashrate = specs.hashrate_th
        default_power = specs.power_watts
        default_cost = specs.typical_price_usd
        hashrate_unit_index = 2  # TH/s
    else:
        default_hashrate = 200.0
        default_power = 3500.0
        default_cost = 4000.0
        hashrate_unit_index = 2  # TH/s

    # Interactive input fields for hardware specs
    miner_hashrate_val = st.sidebar.number_input(
        "礦機算力",
        min_value=0.1,
        value=float(default_hashrate),
        step=1.0,
        format="%.2f",
        help="輸入您挖礦設備的原始運算速度。"
    )
    
    hashrate_unit = st.sidebar.selectbox(
        "算力單位",
        options=["GH/s", "TH/s", "PH/s", "EH/s"],
        index=hashrate_unit_index,
        help="選擇算力級別（例如，現代 ASIC 礦機通常以 TH/s 為單位）。"
    )

    power_watts = st.sidebar.number_input(
        "消耗功率 (瓦特)",
        min_value=0.0,
        value=float(default_power),
        step=50.0,
        help="礦機的功耗（瓦特）。"
    )

    asic_cost_usd = st.sidebar.number_input(
        "ASIC 購買價格 (USD)",
        min_value=0.0,
        value=float(default_cost),
        step=100.0,
        help="購置硬體的成本（在生命週期內折舊）。"
    )

    # Convert the miner hashrate to base H/s for internal calculations
    miner_hashrate_h_s = convert_hashrate(miner_hashrate_val, hashrate_unit, "H/s")

    st.sidebar.markdown("---")

    # 2. NETWORK ASSUMPTIONS (preloaded from API)
    st.sidebar.header("🌐 網路狀態")
    st.sidebar.caption(f"數據同步來源: {live_data.get('source', 'Unknown')}")
    
    btc_price_usd = st.sidebar.number_input(
        "比特幣價格 (USD)",
        min_value=1.0,
        value=float(live_data["btc_price_usd"]),
        step=500.0,
        format="%.2f",
        help="比特幣當前市場價格。動態載入。"
    )

    difficulty = st.sidebar.number_input(
        "全網難度",
        min_value=1.0,
        value=float(live_data["difficulty"]),
        step=1e11,
        format="%.4e",
        help="比特幣網路難度參數。控制出塊時間目標。"
    )

    block_reward_btc = st.sidebar.number_input(
        "區塊獎勵 (BTC)",
        min_value=0.0,
        value=float(live_data["block_reward_btc"]),
        step=0.1,
        help="當前區塊補貼獎勵（每 210,000 個區塊減半一次）。"
    )

    est_tx_fees_btc = st.sidebar.number_input(
        "預估單個區塊交易手續費 (BTC)",
        min_value=0.0,
        value=float(live_data["est_tx_fees_btc"]),
        step=0.01,
        help="預估每個區塊中獎勵給礦工的交易手續費總和。"
    )

    st.sidebar.markdown("---")

    # 3. ELECTRICITY & OPEX CONFIGURATION
    st.sidebar.header("⚡ 電力與營運成本")

    electricity_cost_usd_kwh = st.sidebar.number_input(
        "電費度數價格 (USD/kWh)",
        min_value=0.0,
        value=0.08,
        step=0.01,
        format="%.3f",
        help="每度電（千瓦小時）的電費。利潤的主要驅動因素。"
    )

    pue = st.sidebar.slider(
        "冷卻額外消耗 (PUE)",
        min_value=1.0,
        max_value=2.0,
        value=1.15,
        step=0.05,
        help="能源效率指標。1.15 代表額外消耗 15% 的電量用於冷卻或風扇。"
    )

    maintenance_cost_usd_month = st.sidebar.number_input(
        "託管 / 維護費用 (USD/月)",
        min_value=0.0,
        value=0.0,
        step=10.0,
        help="用於機位託管、監控、維修或保險的每月費用。"
    )

    st.sidebar.markdown("---")

    # 4. SIMULATION & GROWTH PROJECTIONS
    st.sidebar.header("📊 預測與模擬設定")

    difficulty_annual_growth = st.sidebar.slider(
        "年難度增長率 (%)",
        min_value=-50,
        max_value=150,
        value=20,
        step=5,
        help="由於全網算力擴張，預期難度每年增加的百分比。"
    ) / 100.0

    btc_price_annual_growth = st.sidebar.slider(
        "年幣價增長率 (%)",
        min_value=-90,
        max_value=300,
        value=10,
        step=5,
        help="比特幣價格預期的年變動率。"
    ) / 100.0

    simulation_count = st.sidebar.selectbox(
        "蒙特卡洛模擬次數",
        options=[1000, 5000, 10000, 50000, 100000],
        index=2,  # Default 10000
        help="運行的模擬次數。次數越高，曲線越平滑，但計算時間越長。"
    )

    st.sidebar.markdown("---")

    # 5. FINANCIAL ASSUMPTIONS
    st.sidebar.header("📈 財務指標與折現")

    lifetime_months = st.sidebar.number_input(
        "硬體生命週期 (月)",
        min_value=1,
        max_value=120,
        value=36,
        step=12,
        help="在折舊、淘汰或損壞前，礦機預期的運作時間（月）。"
    )

    annual_discount_rate = st.sidebar.slider(
        "年折現率 (%)",
        min_value=0,
        max_value=50,
        value=10,
        step=1,
        help="計算淨現值 (NPV) 所採用的年折現率。"
    ) / 100.0

    # Build the configurations dictionary
    return {
        "miner_hashrate_h_s": miner_hashrate_h_s,
        "miner_hashrate_display": miner_hashrate_val,
        "miner_hashrate_unit": hashrate_unit,
        "power_watts": power_watts,
        "asic_cost_usd": asic_cost_usd,
        "electricity_cost_usd_kwh": electricity_cost_usd_kwh,
        "pue": pue,
        "maintenance_cost_usd_month": maintenance_cost_usd_month,
        "lifetime_months": int(lifetime_months),
        "difficulty": difficulty,
        "block_reward_btc": block_reward_btc,
        "est_tx_fees_btc": est_tx_fees_btc,
        "btc_price_usd": btc_price_usd,
        "difficulty_annual_growth": difficulty_annual_growth,
        "btc_price_annual_growth": btc_price_annual_growth,
        "simulation_count": simulation_count,
        "annual_discount_rate": annual_discount_rate,
        "selected_asic_name": selected_asic_name
    }
