import streamlit as st

import pytest
import math
from core.finance import (
    calculate_opex,
    calculate_expected_revenue,
    calculate_irr,
    calculate_financials,
    run_scenarios
)

def test_calculate_opex() -> None:
    """Tests operational expenditure calculations under varying conditions."""
    # Input conditions: Power: 3000 W, rate: 0.10 USD/kWh, PUE: 1.10, maintenance: 100 USD/month, days: 30
    power = 3000.0
    rate = 0.10
    pue = 1.10
    maint = 100.0
    days = 30.0
    
    opex = calculate_opex(power, rate, pue, maint, days)
    
    # Expected calculations:
    # Elec = (3.0 kW) * 24h/day * 30 days = 2160 kWh
    # Cost = 2160 * 0.10 * 1.10 = 237.6 USD
    # Maint = (100 / 30.416) * 30 = 98.632 USD
    # Expected Total = 237.6 + 98.632 = 336.232 USD
    expected_elec = (power / 1000.0) * 24.0 * days * rate * pue
    expected_maint = (maint / 30.416) * days
    expected_total = expected_elec + expected_maint
    
    assert pytest.approx(opex, rel=1e-5) == expected_total
    
    # Test zero cases
    assert calculate_opex(0.0, rate, pue, maint, days) == expected_maint
    assert calculate_opex(power, rate, pue, maint, 0.0) == 0.0

def test_calculate_expected_revenue() -> None:
    """Verifies that revenue and rewards calculation aligns with expected block discoveries."""
    miner_h = 100 * 1e12
    diff = 80 * 1e12
    reward = 3.125
    fees = 0.15
    price = 60000.0
    days = 30.416
    
    blocks, btc, usd = calculate_expected_revenue(miner_h, diff, reward, fees, price, days)
    
    expected_blocks = (miner_h * (days * 86400.0)) / (diff * (2**32))
    expected_btc = expected_blocks * (reward + fees)
    expected_usd = expected_btc * price
    
    assert pytest.approx(blocks, rel=1e-5) == expected_blocks
    assert pytest.approx(btc, rel=1e-5) == expected_btc
    assert pytest.approx(usd, rel=1e-5) == expected_usd

def test_calculate_irr() -> None:
    """Tests custom IRR bisection solver with normal cash flows."""
    # Test simple cash flow: -100, then 40, 40, 40 (yields positive IRR)
    # Solve 40/(1+r) + 40/(1+r)^2 + 40/(1+r)^3 = 100
    # For r ~ 9.7% or 0.097
    cfs = [-100.0, 40.0, 40.0, 40.0]
    irr = calculate_irr(cfs)
    
    # Calculate NPV with the solved IRR, it should be close to 0
    npv = sum(cf / ((1.0 + irr) ** t) for t, cf in enumerate(cfs))
    assert pytest.approx(npv, abs=1e-4) == 0.0
    
    # Test edge cases where IRR should be NaN or invalid
    assert math.isnan(calculate_irr([-100.0, -50.0, -10.0]))
    assert math.isnan(calculate_irr([100.0, 50.0, 10.0]))

def test_calculate_financials() -> None:
    """Validates the full financials ledger outputs for correct NPV, ROI, and Payback indices."""
    miner_h = 200 * 1e12
    power = 3500.0
    asic_cost = 4000.0
    elec_rate = 0.08
    pue = 1.15
    maint = 0.0
    lifetime_months = 36
    diff = 90 * 1e12
    reward = 3.125
    fees = 0.15
    price = 65000.0
    discount_rate = 0.10
    
    financials = calculate_financials(
        miner_hashrate_h_s=miner_h,
        power_watts=power,
        asic_cost_usd=asic_cost,
        electricity_cost_usd_kwh=elec_rate,
        pue=pue,
        maintenance_cost_usd_month=maint,
        lifetime_months=lifetime_months,
        difficulty=diff,
        block_reward_btc=reward,
        est_tx_fees_btc=fees,
        btc_price_usd=price,
        annual_discount_rate=discount_rate
    )
    
    assert financials["roi"] is not None
    assert financials["npv"] is not None
    assert "irr_annual" in financials
    assert len(financials["cash_flows"]) == lifetime_months + 1
    assert financials["cash_flows"][0] == -asic_cost
    
    # Operational break-evens should be positive
    assert financials["breakeven_btc_price"] > 0.0
    assert financials["breakeven_difficulty"] > 0.0

def test_run_scenarios() -> None:
    """Verifies that scenario run generates partitions for Bull, Neutral, and Bear settings."""
    miner_h = 200 * 1e12
    power = 3500.0
    asic_cost = 4000.0
    elec_rate = 0.08
    pue = 1.15
    maint = 0.0
    lifetime_months = 36
    diff = 90 * 1e12
    reward = 3.125
    fees = 0.15
    price = 65000.0
    discount_rate = 0.10
    
    results = run_scenarios(
        miner_hashrate_h_s=miner_h,
        power_watts=power,
        asic_cost_usd=asic_cost,
        electricity_cost_usd_kwh=elec_rate,
        pue=pue,
        maintenance_cost_usd_month=maint,
        lifetime_months=lifetime_months,
        base_difficulty=diff,
        block_reward_btc=reward,
        est_tx_fees_btc=fees,
        base_btc_price_usd=price,
        annual_discount_rate=discount_rate
    )
    
    assert "Bull Market" in results
    assert "Neutral Market" in results
    assert "Bear Market" in results
    
    # Bull Market pricing should be higher than Bear Market pricing
    assert results["Bull Market"]["adjusted_price"] > results["Bear Market"]["adjusted_price"]

def test_irr_and_payback_edge_cases() -> None:
    """Verifies that IRR bisection search boundaries and payback loops work on edge margins."""
    # Test completely unviable project (should return nan for IRR)
    unviable_cfs = [-100.0, -10.0, -5.0, -2.0]
    assert math.isnan(calculate_irr(unviable_cfs))
    
    # Test a super profitable project to verify payback breaks early
    miner_h = 1e20  # Massive hashrate
    power = 1000.0
    asic_cost = 10.0
    elec_rate = 0.01
    pue = 1.0
    maint = 0.0
    lifetime_months = 12
    diff = 1e9  # Tiny difficulty
    reward = 3.125
    fees = 0.15
    price = 65000.0
    discount_rate = 0.10
    
    fin = calculate_financials(
        miner_hashrate_h_s=miner_h,
        power_watts=power,
        asic_cost_usd=asic_cost,
        electricity_cost_usd_kwh=elec_rate,
        pue=pue,
        maintenance_cost_usd_month=maint,
        lifetime_months=lifetime_months,
        difficulty=diff,
        block_reward_btc=reward,
        est_tx_fees_btc=fees,
        btc_price_usd=price,
        annual_discount_rate=discount_rate
    )
    # Since it's extremely profitable, payback must occur in month 1
    assert fin["payback_period_months"] == 1
    
    # Test 0 hashrate (triggers infinity breakevens and payback)
    fin_zero = calculate_financials(
        miner_hashrate_h_s=0.0,
        power_watts=power,
        asic_cost_usd=asic_cost,
        electricity_cost_usd_kwh=elec_rate,
        pue=pue,
        maintenance_cost_usd_month=maint,
        lifetime_months=lifetime_months,
        difficulty=diff,
        block_reward_btc=reward,
        est_tx_fees_btc=fees,
        btc_price_usd=price,
        annual_discount_rate=discount_rate
    )
    assert fin_zero["breakeven_btc_price"] == float("inf")
    assert fin_zero["breakeven_difficulty"] == float("inf")
    assert fin_zero["payback_period_months"] == float("inf")


# ====== 自動生成的測試執行區塊 ======
if __name__ == "__main__":
    st.write("---")
    st.subheader("函數測試區塊")
    if st.button("執行 test_calculate_opex"):
        try:
            res = test_calculate_opex() # 請視需要自行補上參數
            st.write("執行結果:", res)
        except Exception as e:
            st.error(f"執行出錯，可能需要提供參數：{e}")
    if st.button("執行 test_calculate_expected_revenue"):
        try:
            res = test_calculate_expected_revenue() # 請視需要自行補上參數
            st.write("執行結果:", res)
        except Exception as e:
            st.error(f"執行出錯，可能需要提供參數：{e}")
    if st.button("執行 test_calculate_irr"):
        try:
            res = test_calculate_irr() # 請視需要自行補上參數
            st.write("執行結果:", res)
        except Exception as e:
            st.error(f"執行出錯，可能需要提供參數：{e}")
    if st.button("執行 test_calculate_financials"):
        try:
            res = test_calculate_financials() # 請視需要自行補上參數
            st.write("執行結果:", res)
        except Exception as e:
            st.error(f"執行出錯，可能需要提供參數：{e}")
    if st.button("執行 test_run_scenarios"):
        try:
            res = test_run_scenarios() # 請視需要自行補上參數
            st.write("執行結果:", res)
        except Exception as e:
            st.error(f"執行出錯，可能需要提供參數：{e}")
    if st.button("執行 test_irr_and_payback_edge_cases"):
        try:
            res = test_irr_and_payback_edge_cases() # 請視需要自行補上參數
            st.write("執行結果:", res)
        except Exception as e:
            st.error(f"執行出錯，可能需要提供參數：{e}")
