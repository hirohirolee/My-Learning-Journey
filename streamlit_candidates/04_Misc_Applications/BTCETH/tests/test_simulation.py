import streamlit as st
st.title('test_simulation.py - 自動化展示')
st.info('這是從原專案腳本自動包裝產生的互動式介面。')

import pytest
import numpy as np
from core.simulation import run_monte_carlo_simulation

def test_monte_carlo_simulation_outputs() -> None:
    """Verifies that the simulation engine executes and produces all required data structures."""
    miner_h = 200 * 1e12  # 200 TH/s
    power = 3500.0
    asic_cost = 4000.0
    elec_rate = 0.08
    pue = 1.15
    maint = 0.0
    lifetime_months = 12
    diff = 90 * 1e12
    reward = 3.125
    fees = 0.15
    price = 65000.0
    
    sim_results = run_monte_carlo_simulation(
        miner_hashrate_h_s=miner_h,
        power_watts=power,
        asic_cost_usd=asic_cost,
        electricity_cost_usd_kwh=elec_rate,
        pue=pue,
        maintenance_cost_usd_month=maint,
        lifetime_months=lifetime_months,
        initial_difficulty=diff,
        difficulty_annual_growth=0.10,
        block_reward_btc=reward,
        est_tx_fees_btc=fees,
        btc_price_usd=price,
        btc_price_annual_growth=0.20,
        simulation_count=100
    )
    
    # Assert keys exist
    expected_keys = [
        "success_rate",
        "profit_rate",
        "mean_blocks_mined",
        "max_blocks_mined",
        "mean_profit_usd",
        "median_profit_usd",
        "std_profit_usd",
        "payback_months",
        "mean_payback_months",
        "blocks_distribution",
        "final_profits",
        "cash_flow_paths",
        "cf_percentiles",
        "mean_cf_path",
        "monthly_opex",
        "total_opex"
    ]
    for key in expected_keys:
        assert key in sim_results
        
    # Check data types and boundaries
    assert 0.0 <= sim_results["success_rate"] <= 1.0
    assert 0.0 <= sim_results["profit_rate"] <= 1.0
    assert sim_results["mean_blocks_mined"] >= 0.0
    assert len(sim_results["final_profits"]) == 100
    assert len(sim_results["mean_cf_path"]) == lifetime_months + 1
    
    # Check that block distribution has 0, 1, 2, 3 blocks
    for i in range(4):
        assert i in sim_results["blocks_distribution"]
        
    # Total opex should be positive
    assert sim_results["total_opex"] > 0


# ====== 自動生成的測試執行區塊 ======
if __name__ == "__main__":
    st.write("---")
    st.subheader("函數測試區塊")
    if st.button("執行 test_monte_carlo_simulation_outputs"):
        try:
            res = test_monte_carlo_simulation_outputs() # 請視需要自行補上參數
            st.write("執行結果:", res)
        except Exception as e:
            st.error(f"執行出錯，可能需要提供參數：{e}")
