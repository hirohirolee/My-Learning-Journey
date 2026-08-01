import streamlit as st
st.title('test_probability.py - 自動化展示')
st.info('這是從原專案腳本自動包裝產生的互動式介面。')

import pytest
import math
from core.difficulty import convert_hashrate
from core.probability import (
    get_block_mining_probability_per_second,
    get_expected_blocks_in_period,
    get_poisson_probability_of_success,
    get_binomial_probability_of_success,
    calculate_waiting_time_metrics,
    get_probability_over_horizons
)

def test_hashrate_conversions() -> None:
    """Verifies that hashrate unit conversions compute correct magnitudes."""
    # Test TH/s to H/s
    assert convert_hashrate(1.0, "TH/s", "H/s") == 1e12
    # Test GH/s to TH/s
    assert convert_hashrate(1000.0, "GH/s", "TH/s") == 1.0
    # Test EH/s to H/s
    assert convert_hashrate(1.0, "EH/s", "H/s") == 1e18
    # Test EH/s to PH/s
    assert convert_hashrate(2.5, "EH/s", "PH/s") == 2500.0

    # Test error raising
    with pytest.raises(ValueError):
        convert_hashrate(1.0, "UNKNOWN", "H/s")

def test_block_mining_probability_per_second() -> None:
    """Verifies that the block probability per second formula yields correct values."""
    # Standard values: H = 100 TH/s = 1e14 H/s, D = 80,000,000,000,000
    miner_h = 100 * 1e12
    diff = 80_000_000_000_000
    
    prob = get_block_mining_probability_per_second(miner_h, diff)
    expected = miner_h / (diff * (2**32))
    
    assert prob == expected
    assert 0.0 < prob < 1.0
    
    # Test edge cases
    assert get_block_mining_probability_per_second(0, diff) == 0.0
    assert get_block_mining_probability_per_second(miner_h, 0) == 0.0

def test_expected_blocks_in_period() -> None:
    """Verifies lambda parameter matches mathematical expectations."""
    miner_h = 200 * 1e12
    diff = 90_000_000_000_000
    day_secs = 86400.0
    
    lam = get_expected_blocks_in_period(miner_h, diff, day_secs)
    expected = (miner_h * day_secs) / (diff * (2**32))
    
    assert pytest.approx(lam, rel=1e-9) == expected

def test_poisson_probability_of_success() -> None:
    """Ensures Poisson cumulative success calculations align with statistical baselines."""
    # If expected blocks (lambda) is extremely large, probability should approach 1.0
    large_prob = get_poisson_probability_of_success(
        miner_hashrate_h_s=1e20,  # Ridiculous hashrate
        difficulty=1e10,          # Small difficulty
        period_seconds=86400.0
    )
    assert large_prob == 1.0

    # If hashrate is 0, success probability is 0
    assert get_poisson_probability_of_success(0.0, 1e12, 3600.0) == 0.0

def test_binomial_probability_of_success() -> None:
    """Tests the hashrate fraction binomial model."""
    miner_h = 1e12
    net_h = 1e14
    
    # Binomial probability of ≥1 block in 6000 seconds (10 blocks mined total by network)
    prob = get_binomial_probability_of_success(miner_h, net_h, 6000.0, 1)
    
    # Expected: 1 - (1 - p_block)^10 where p_block = 1e12 / 1e14 = 0.01
    expected = 1.0 - (0.99 ** 10)
    assert pytest.approx(prob, rel=1e-5) == expected

def test_waiting_time_metrics() -> None:
    """Verifies that mean, median, and 95% confidence intervals calculate correctly."""
    miner_h = 150 * 1e12
    diff = 85_000_000_000_000
    
    metrics = calculate_waiting_time_metrics(miner_h, diff)
    
    expected_mean = 1.0 / get_block_mining_probability_per_second(miner_h, diff)
    expected_median = expected_mean * math.log(2.0)
    expected_ci_lower = -math.log(0.975) * expected_mean
    expected_ci_upper = -math.log(0.025) * expected_mean
    
    assert metrics["expected_waiting_time_seconds"] == expected_mean
    assert metrics["median_waiting_time_seconds"] == expected_median
    assert metrics["ci_95_lower_seconds"] == expected_ci_lower
    assert metrics["ci_95_upper_seconds"] == expected_ci_upper

    # Test edge cases
    empty_metrics = calculate_waiting_time_metrics(0.0, diff)
    assert empty_metrics["expected_waiting_time_seconds"] == float("inf")

def test_probability_over_horizons() -> None:
    """Validates structure and value range of output list for time horizons."""
    miner_h = 200 * 1e12
    diff = 90_000_000_000_000
    
    horizons = get_probability_over_horizons(miner_h, diff)
    assert len(horizons) > 0
    assert horizons[0]["horizon"] == "1 day"
    assert "probability" in horizons[0]
    assert 0.0 <= horizons[0]["probability"] <= 1.0

def test_forecast_difficulty_and_hashrate() -> None:
    """Verifies difficulty and hashrate forecasting functions, including growth floors."""
    from core.difficulty import forecast_difficulty, forecast_hashrate
    # Standard check
    assert forecast_difficulty(100.0, 0.10, 2.0) == 100.0 * (1.10 ** 2.0)
    assert forecast_hashrate(1000.0, 0.10, 2.0) == 1000.0 * (1.10 ** 2.0)
    
    # Growth rate under -1.0 gets capped at -1.0 (leads to 0 difficulty/hashrate)
    assert forecast_difficulty(100.0, -1.5, 2.0) == 0.0
    assert forecast_hashrate(1000.0, -1.5, 2.0) == 0.0


# ====== 自動生成的測試執行區塊 ======
if __name__ == "__main__":
    st.write("---")
    st.subheader("函數測試區塊")
    if st.button("執行 test_hashrate_conversions"):
        try:
            res = test_hashrate_conversions() # 請視需要自行補上參數
            st.write("執行結果:", res)
        except Exception as e:
            st.error(f"執行出錯，可能需要提供參數：{e}")
    if st.button("執行 test_block_mining_probability_per_second"):
        try:
            res = test_block_mining_probability_per_second() # 請視需要自行補上參數
            st.write("執行結果:", res)
        except Exception as e:
            st.error(f"執行出錯，可能需要提供參數：{e}")
    if st.button("執行 test_expected_blocks_in_period"):
        try:
            res = test_expected_blocks_in_period() # 請視需要自行補上參數
            st.write("執行結果:", res)
        except Exception as e:
            st.error(f"執行出錯，可能需要提供參數：{e}")
    if st.button("執行 test_poisson_probability_of_success"):
        try:
            res = test_poisson_probability_of_success() # 請視需要自行補上參數
            st.write("執行結果:", res)
        except Exception as e:
            st.error(f"執行出錯，可能需要提供參數：{e}")
    if st.button("執行 test_binomial_probability_of_success"):
        try:
            res = test_binomial_probability_of_success() # 請視需要自行補上參數
            st.write("執行結果:", res)
        except Exception as e:
            st.error(f"執行出錯，可能需要提供參數：{e}")
    if st.button("執行 test_waiting_time_metrics"):
        try:
            res = test_waiting_time_metrics() # 請視需要自行補上參數
            st.write("執行結果:", res)
        except Exception as e:
            st.error(f"執行出錯，可能需要提供參數：{e}")
    if st.button("執行 test_probability_over_horizons"):
        try:
            res = test_probability_over_horizons() # 請視需要自行補上參數
            st.write("執行結果:", res)
        except Exception as e:
            st.error(f"執行出錯，可能需要提供參數：{e}")
    if st.button("執行 test_forecast_difficulty_and_hashrate"):
        try:
            res = test_forecast_difficulty_and_hashrate() # 請視需要自行補上參數
            st.write("執行結果:", res)
        except Exception as e:
            st.error(f"執行出錯，可能需要提供參數：{e}")
