import streamlit as st

import math
from typing import Dict, List, Tuple, Any
import scipy.stats as stats
from core.difficulty import convert_hashrate

# 時間區段（單位：秒）
TIME_HORIZONS: Dict[str, float] = {
    "1 day": 86400.0,
    "7 days": 7 * 86400.0,
    "30 days": 30 * 86400.0,
    "90 days": 90 * 86400.0,
    "180 days": 180 * 86400.0,
    "365 days": 365 * 86400.0,
    "730 days": 730 * 86400.0,
    "1825 days": 1825 * 86400.0,
}

def get_block_mining_probability_per_second(
    miner_hashrate_h_s: float,
    difficulty: float
) -> float:
    """計算單個礦機在每一秒內挖出區塊的機率。
    
    公式: p = H / (D * 2^32)
    
    Args:
        miner_hashrate_h_s (float): 礦機算力 (H/s)。
        difficulty (float): 全網難度。
        
    Returns:
        float: 每秒出塊機率。
    """
    if miner_hashrate_h_s <= 0 or difficulty <= 0:
        return 0.0
    return miner_hashrate_h_s / (difficulty * (2**32))

def get_expected_blocks_in_period(
    miner_hashrate_h_s: float,
    difficulty: float,
    period_seconds: float
) -> float:
    """計算給定時間區段內預期挖出的區塊數量（Poisson lambda 參數）。
    
    公式: lambda = p * T = (H * T) / (D * 2^32)
    
    Args:
        miner_hashrate_h_s (float): 礦機算力 (H/s)。
        difficulty (float): 全網難度。
        period_seconds (float): 時間長度（秒）。
        
    Returns:
        float: 期望挖出區塊數 (lambda)。
    """
    p = get_block_mining_probability_per_second(miner_hashrate_h_s, difficulty)
    return p * period_seconds

def get_poisson_probability_of_success(
    miner_hashrate_h_s: float,
    difficulty: float,
    period_seconds: float,
    min_blocks: int = 1
) -> float:
    """運用 Poisson 分布計算給定時間內挖出至少 `min_blocks` 個區塊的機率。
    
    公式: P(X >= k) = 1 - CDF(k-1, lambda)
    
    Args:
        miner_hashrate_h_s (float): 礦機算力 (H/s)。
        difficulty (float): 全網難度。
        period_seconds (float): 時間長度（秒）。
        min_blocks (int): 成功所需的最低出塊數（預設為 1）。
        
    Returns:
        float: 挖出成功率 (0.0 到 1.0)。
    """
    lam = get_expected_blocks_in_period(miner_hashrate_h_s, difficulty, period_seconds)
    if lam <= 0:
        return 0.0
    
    # sf 是生存函數 (Survival Function): 1 - cdf
    # P(X >= k) = P(X > k-1) = sf(k-1)
    return float(stats.poisson.sf(min_blocks - 1, lam))

def get_binomial_probability_of_success(
    miner_hashrate_h_s: float,
    network_hashrate_h_s: float,
    period_seconds: float,
    min_blocks: int = 1
) -> float:
    """運用 Binomial (二項) 分布計算挖出至少 `min_blocks` 個區塊的機率。
    
    假設網路平均出塊時間為 600 秒以計算總區塊試驗次數 N。
    公式: P(Y >= k) = 1 - CDF(k-1, N, p_block)
    其中 p_block = 礦機算力 / 全網算力
    
    Args:
        miner_hashrate_h_s (float): 礦機算力 (H/s)。
        network_hashrate_h_s (float): 全網算力 (H/s)。
        period_seconds (float): 時間長度（秒）。
        min_blocks (int): 成功所需的最低出塊數。
        
    Returns:
        float: 挖出成功率 (0.0 到 1.0)。
    """
    if miner_hashrate_h_s <= 0 or network_hashrate_h_s <= 0 or period_seconds < 600.0:
        return 0.0
    
    p_block = miner_hashrate_h_s / network_hashrate_h_s
    if p_block >= 1.0:
        return 1.0
        
    n_trials = int(round(period_seconds / 600.0))
    if n_trials < min_blocks:
        return 0.0
        
    return float(stats.binom.sf(min_blocks - 1, n_trials, p_block))

def calculate_waiting_time_metrics(
    miner_hashrate_h_s: float,
    difficulty: float
) -> Dict[str, float]:
    """計算出塊的預期等待時間和置信區間。
    
    假設出塊間隔符合指數分布 (Exponential Distribution)。
    
    Args:
        miner_hashrate_h_s (float): 礦機算力 (H/s)。
        difficulty (float): 全網難度。
        
    Returns:
        Dict[str, float]: 包含以下指標的字典:
            - "expected_waiting_time_seconds" (預期平均等待秒數)
            - "median_waiting_time_seconds" (中位數等待秒數)
            - "ci_95_lower_seconds" (95%置信區間下限)
            - "ci_95_upper_seconds" (95%置信區間上限)
    """
    p = get_block_mining_probability_per_second(miner_hashrate_h_s, difficulty)
    
    if p <= 0:
        return {
            "expected_waiting_time_seconds": float("inf"),
            "median_waiting_time_seconds": float("inf"),
            "ci_95_lower_seconds": float("inf"),
            "ci_95_upper_seconds": float("inf"),
        }
        
    expected_wait = 1.0 / p
    median_wait = expected_wait * math.log(2.0)
    
    # 指數分布的 95% 置信區間：
    # 下限 (2.5% 累積率): F(t) = 0.025 -> t = -ln(0.975) * expected_wait
    # 上限 (97.5% 累積率): F(t) = 0.975 -> t = -ln(0.025) * expected_wait
    ci_lower = -math.log(0.975) * expected_wait
    ci_upper = -math.log(0.025) * expected_wait
    
    return {
        "expected_waiting_time_seconds": expected_wait,
        "median_waiting_time_seconds": median_wait,
        "ci_95_lower_seconds": ci_lower,
        "ci_95_upper_seconds": ci_upper,
    }

def get_probability_over_horizons(
    miner_hashrate_h_s: float,
    difficulty: float
) -> List[Dict[str, Any]]:
    """生成一組預先定義時間跨度下的挖出至少 1 個區塊的機率。
    
    Args:
        miner_hashrate_h_s (float): 礦機算力 (H/s)。
        difficulty (float): 全網難度。
        
    Returns:
        List[Dict[str, Any]]: 每個時間跨度下的計算結果列表。
    """
    results = []
    for horizon_name, seconds in TIME_HORIZONS.items():
        prob = get_poisson_probability_of_success(miner_hashrate_h_s, difficulty, seconds)
        results.append({
            "horizon": horizon_name,
            "seconds": seconds,
            "probability": prob
        })
    return results


# ====== 自動生成的測試執行區塊 ======
if __name__ == "__main__":
    st.write("---")
    st.subheader("函數測試區塊")
    if st.button("執行 get_block_mining_probability_per_second"):
        try:
            res = get_block_mining_probability_per_second() # 請視需要自行補上參數
            st.write("執行結果:", res)
        except Exception as e:
            st.error(f"執行出錯，可能需要提供參數：{e}")
    if st.button("執行 get_expected_blocks_in_period"):
        try:
            res = get_expected_blocks_in_period() # 請視需要自行補上參數
            st.write("執行結果:", res)
        except Exception as e:
            st.error(f"執行出錯，可能需要提供參數：{e}")
    if st.button("執行 get_poisson_probability_of_success"):
        try:
            res = get_poisson_probability_of_success() # 請視需要自行補上參數
            st.write("執行結果:", res)
        except Exception as e:
            st.error(f"執行出錯，可能需要提供參數：{e}")
    if st.button("執行 get_binomial_probability_of_success"):
        try:
            res = get_binomial_probability_of_success() # 請視需要自行補上參數
            st.write("執行結果:", res)
        except Exception as e:
            st.error(f"執行出錯，可能需要提供參數：{e}")
    if st.button("執行 calculate_waiting_time_metrics"):
        try:
            res = calculate_waiting_time_metrics() # 請視需要自行補上參數
            st.write("執行結果:", res)
        except Exception as e:
            st.error(f"執行出錯，可能需要提供參數：{e}")
    if st.button("執行 get_probability_over_horizons"):
        try:
            res = get_probability_over_horizons() # 請視需要自行補上參數
            st.write("執行結果:", res)
        except Exception as e:
            st.error(f"執行出錯，可能需要提供參數：{e}")
