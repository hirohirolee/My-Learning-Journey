import streamlit as st

import numpy as np
from typing import Any, Dict, List
from btc_core.finance import calculate_opex

def run_monte_carlo_simulation(
    miner_hashrate_h_s: float,
    power_watts: float,
    asic_cost_usd: float,
    electricity_cost_usd_kwh: float,
    pue: float,
    maintenance_cost_usd_month: float,
    lifetime_months: int,
    initial_difficulty: float,
    difficulty_annual_growth: float,
    block_reward_btc: float,
    est_tx_fees_btc: float,
    btc_price_usd: float,
    btc_price_annual_growth: float,
    simulation_count: int = 10000
) -> Dict[str, Any]:
    """執行比特幣單機挖礦的向量化蒙特卡洛模擬。
    
    將月度區塊發現模擬為隨時間變化的 Poisson 隨機過程，並考慮網路難度與比特幣價格的年增長複利效應。
    
    Args:
        miner_hashrate_h_s (float): 礦機算力 (H/s)。
        power_watts (float): ASIC 礦機功耗（瓦特）。
        asic_cost_usd (float): 初始 ASIC 硬體購置費用。
        electricity_cost_usd_kwh (float): 電費單價 (USD/kWh)。
        pue (float): 電源使用效率 (PUE)。
        maintenance_cost_usd_month (float): 每月運維費用。
        lifetime_months (int): 模擬項目生命週期長度（月）。
        initial_difficulty (float): 初始全網難度。
        difficulty_annual_growth (float): 難度年增長率（例如 0.10 代表 10%）。
        block_reward_btc (float): 當前區塊補貼獎勵 (BTC)。
        est_tx_fees_btc (float): 預估單區塊手續費 (BTC)。
        btc_price_usd (float): 比特幣初始價格。
        btc_price_annual_growth (float): 比特幣價格年增長率（例如 0.20 代表 20%）。
        simulation_count (int): 模擬路徑總數。
        
    Returns:
        Dict[str, Any]: 模擬統計數據、現金流軌跡及概率分布結果。
    """
    days_per_month = 30.416
    seconds_per_month = days_per_month * 86400.0
    
    # 計算月度營運成本
    monthly_opex = calculate_opex(
        power_watts=power_watts,
        electricity_cost_usd_kwh=electricity_cost_usd_kwh,
        pue=pue,
        maintenance_cost_usd_month=maintenance_cost_usd_month,
        days=days_per_month
    )

    # 1. 建立各月份的全網難度與比特幣價格增長曲線向量
    months = np.arange(1, lifetime_months + 1)
    
    # 折算至月度增長率
    g_diff_m = (1.0 + difficulty_annual_growth) ** (1.0 / 12.0) - 1.0
    g_price_m = (1.0 + btc_price_annual_growth) ** (1.0 / 12.0) - 1.0
    
    # 獲取每月的難度與幣價數值向量
    diff_schedule = initial_difficulty * ((1.0 + g_diff_m) ** (months - 1))
    price_schedule = btc_price_usd * ((1.0 + g_price_m) ** (months - 1))
    
    # 2. 計算每月預期的 Poisson 期望出塊數 (lambda schedule)
    # lambda_m = H * T_m / (D_m * 2^32)
    lambda_schedule = (miner_hashrate_h_s * seconds_per_month) / (diff_schedule * (2**32))
    
    # 3. 使用 NumPy 的向量化 Poisson 生成器模擬出塊情況
    # 形狀: (simulation_count, lifetime_months)
    blocks_mined = np.zeros((simulation_count, lifetime_months), dtype=int)
    for m in range(lifetime_months):
        blocks_mined[:, m] = np.random.poisson(lam=lambda_schedule[m], size=simulation_count)
        
    # 4. 計算每條模擬路徑下的月度財務數據
    block_val_btc = block_reward_btc + est_tx_fees_btc
    
    # 月度收益: 出塊數 * 單個區塊價值 (BTC) * 當月比特幣價格
    # 形狀: (simulation_count, lifetime_months)
    monthly_revenue = blocks_mined * block_val_btc * price_schedule
    
    # 月度淨現金流: 收益 - 電費等營運成本
    monthly_net_profit = monthly_revenue - monthly_opex
    
    # 5. 計算各路徑下的累計項目現金流軌跡
    # 欄位 0 為月份 0 支出（即 ASIC 硬體購入成本）
    # 形狀: (simulation_count, lifetime_months + 1)
    cash_flow_paths = np.zeros((simulation_count, lifetime_months + 1))
    cash_flow_paths[:, 0] = -asic_cost_usd
    cash_flow_paths[:, 1:] = np.cumsum(monthly_net_profit, axis=1) - asic_cost_usd

    # 6. 分析模擬結果
    total_blocks_mined = np.sum(blocks_mined, axis=1)
    final_net_profits = cash_flow_paths[:, -1]
    
    # 檢測各模擬路徑下首次回本（累計現金流 >= 0）的月份
    payback_months = np.full(simulation_count, np.nan)
    for i in range(simulation_count):
        payback_indices = np.where(cash_flow_paths[i, :] >= 0)[0]
        if len(payback_indices) > 0:
            payback_months[i] = payback_indices[0]  # 第一個非負數月份即為回本月

    # 計算統計指標
    success_count = np.sum(total_blocks_mined > 0)
    success_rate = float(success_count / simulation_count)
    
    profitable_count = np.sum(final_net_profits > 0)
    profit_rate = float(profitable_count / simulation_count)

    # 統計已挖出區塊數的機率分布 (Frequency Distribution)
    unique_blocks, counts = np.unique(total_blocks_mined, return_counts=True)
    block_dist = {}
    for val, count in zip(unique_blocks, counts):
        block_dist[int(val)] = float(count / simulation_count)

    # 預先填充 0 至 3 的區塊區間，以便前端 Plotly 繪圖完美渲染
    for val in range(4):
        if val not in block_dist:
            block_dist[val] = 0.0

    # 計算不同百分位數 (Percentiles) 的現金流路徑，用以在前端渲染置信包絡線
    percentiles = [5, 25, 50, 75, 95]
    cf_percentiles = {}
    for p in percentiles:
        cf_percentiles[p] = np.percentile(cash_flow_paths, p, axis=0).tolist()

    # 計算平均现金流軌跡
    mean_cf_path = np.mean(cash_flow_paths, axis=0).tolist()

    return {
        "success_rate": success_rate,
        "profit_rate": profit_rate,
        "mean_blocks_mined": float(np.mean(total_blocks_mined)),
        "max_blocks_mined": int(np.max(total_blocks_mined)),
        "mean_profit_usd": float(np.mean(final_net_profits)),
        "median_profit_usd": float(np.median(final_net_profits)),
        "std_profit_usd": float(np.std(final_net_profits)),
        "payback_months": payback_months[~np.isnan(payback_months)].tolist(),
        "mean_payback_months": float(np.nanmean(payback_months)) if not np.all(np.isnan(payback_months)) else float("inf"),
        "blocks_distribution": block_dist,
        "final_profits": final_net_profits.tolist(),
        "cash_flow_paths": cash_flow_paths.tolist(),  # 完整路徑矩陣
        "cf_percentiles": cf_percentiles,
        "mean_cf_path": mean_cf_path,
        "monthly_opex": monthly_opex,
        "total_opex": monthly_opex * lifetime_months,
    }


# ====== 自動生成的測試執行區塊 ======
if __name__ == "__main__":
    st.write("---")
    st.subheader("函數測試區塊")
    if st.button("執行 run_monte_carlo_simulation"):
        try:
            res = run_monte_carlo_simulation() # 請視需要自行補上參數
            st.write("執行結果:", res)
        except Exception as e:
            st.error(f"執行出錯，可能需要提供參數：{e}")
