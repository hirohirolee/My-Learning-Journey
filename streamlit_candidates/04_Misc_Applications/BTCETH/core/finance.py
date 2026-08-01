import streamlit as st

import math
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import scipy.optimize as optimize
from core.probability import get_expected_blocks_in_period

def calculate_opex(
    power_watts: float,
    electricity_cost_usd_kwh: float,
    pue: float,
    maintenance_cost_usd_month: float,
    days: float
) -> float:
    """計算給定天數內運作所產生的營運支出 (OpEx)。
    
    公式:
        電費 = (功耗 / 1000) * 24 * 電費價格 * PUE * 天數
        總營運成本 = 電費 + (每月維護費 / 30.416) * 天數
        
    Args:
        power_watts (float): ASIC 礦機功耗（瓦特）。
        electricity_cost_usd_kwh (float): 電費價格 (USD/kWh)。
        pue (float): 電源使用效率（冷卻能效 overhead，例如 1.15）。
        maintenance_cost_usd_month (float): 每月固定維護/託管費用。
        days (float): 天數。
        
    Returns:
        float: 總營運成本 (OpEx)，以 USD 計。
    """
    if days <= 0:
        return 0.0
        
    electricity_kwh = (max(0.0, power_watts) / 1000.0) * 24.0 * days
    electricity_cost = electricity_kwh * electricity_cost_usd_kwh * pue
    
    # 將每月天數標準化為 30.416 天
    maintenance_cost = (maintenance_cost_usd_month / 30.416) * days
    
    return electricity_cost + maintenance_cost

def calculate_expected_revenue(
    miner_hashrate_h_s: float,
    difficulty: float,
    block_reward_btc: float,
    est_tx_fees_btc: float,
    btc_price_usd: float,
    days: float
) -> Tuple[float, float, float]:
    """計算預期出塊數、預期挖出的 BTC 總數，以及換算的 USD 總收益。
    
    Args:
        miner_hashrate_h_s (float): 礦機算力 (H/s)。
        difficulty (float): 全網難度。
        block_reward_btc (float): 當前區塊補貼獎勵 (BTC)。
        est_tx_fees_btc (float): 當前區塊估計手續費獎勵 (BTC)。
        btc_price_usd (float): 比特幣價格 (USD)。
        days (float): 計算天數。
        
    Returns:
        Tuple[float, float, float]: (預期出塊數, 預期挖出 BTC 數, 預期換算 USD 收益)。
    """
    period_seconds = days * 86400.0
    expected_blocks = get_expected_blocks_in_period(miner_hashrate_h_s, difficulty, period_seconds)
    
    total_block_val_btc = block_reward_btc + est_tx_fees_btc
    expected_btc = expected_blocks * total_block_val_btc
    expected_usd = expected_btc * btc_price_usd
    
    return expected_blocks, expected_btc, expected_usd

def calculate_irr(cash_flows: List[float]) -> float:
    """計算一組定期現金流的年化內部收益率 (IRR)。
    
    使用二分法 (Bisection Method) 來求解 NPV 等式中的折現率根。
    
    Args:
        cash_flows (List[float]): 包含初始投資（負值）在內的現金流列表。
        
    Returns:
        float: IRR 數值（小數形式），若無解則返回 NaN。
    """
    if not cash_flows or all(cf >= 0 for cf in cash_flows) or all(cf <= 0 for cf in cash_flows):
        return float("nan")
        
    def npv_func(r: float) -> float:
        total = 0.0
        for t, cf in enumerate(cash_flows):
            total += cf / ((1.0 + r) ** t)
        return total

    # 二分搜尋範圍
    low, high = -0.99, 10.0
    
    # 若根超出初始設定範圍，則動態向右擴張邊界
    f_low = npv_func(low)
    f_high = npv_func(high)
    
    if f_low * f_high > 0:
        for _ in range(5):
            high *= 2.0
            f_high = npv_func(high)
            if f_low * f_high < 0:
                break
        else:
            return float("nan")
            
    try:
        root = optimize.brentq(npv_func, low, high, xtol=1e-6)
        return float(root)
    except ValueError:
        return float("nan")

def calculate_financials(
    miner_hashrate_h_s: float,
    power_watts: float,
    asic_cost_usd: float,
    electricity_cost_usd_kwh: float,
    pue: float,
    maintenance_cost_usd_month: float,
    lifetime_months: int,
    difficulty: float,
    block_reward_btc: float,
    est_tx_fees_btc: float,
    btc_price_usd: float,
    annual_discount_rate: float
) -> Dict[str, Any]:
    """完整評估挖礦項目的月度現金流、NPV、IRR、盈虧平衡邊界與投資回報率 (ROI)。
    
    Args:
        miner_hashrate_h_s (float): 礦機算力 (H/s)。
        power_watts (float): ASIC 礦機功耗（瓦特）。
        asic_cost_usd (float): 初始 ASIC 硬體購置費用。
        electricity_cost_usd_kwh (float): 電費單價 (USD/kWh)。
        pue (float): 電源使用效率 (PUE)。
        maintenance_cost_usd_month (float): 每月維護/機位費用。
        lifetime_months (int): 礦機使用年限（月）。
        difficulty (float): 全網難度。
        block_reward_btc (float): 區塊補貼金額。
        est_tx_fees_btc (float): 預期手續費金額。
        btc_price_usd (float): 比特幣當前幣價。
        annual_discount_rate (float): 年折現率（用於 NPV）。
        
    Returns:
        Dict[str, Any]: 財務指標明細字典。
    """
    days_per_month = 30.416
    monthly_discount_rate = (1.0 + annual_discount_rate) ** (1.0 / 12.0) - 1.0
    
    # 計算月度營運成本
    monthly_opex = calculate_opex(
        power_watts, electricity_cost_usd_kwh, pue, maintenance_cost_usd_month, days_per_month
    )
    expected_blocks, expected_btc, expected_revenue_usd = calculate_expected_revenue(
        miner_hashrate_h_s, difficulty, block_reward_btc, est_tx_fees_btc, btc_price_usd, days_per_month
    )
    monthly_net_profit = expected_revenue_usd - monthly_opex

    # 生成項目現金流陣列
    # 月份 0: 支出初始 ASIC 成本
    cash_flows = [-asic_cost_usd] + [monthly_net_profit] * lifetime_months
    
    # 計算項目淨現值 (NPV)
    npv = -asic_cost_usd
    for t in range(1, lifetime_months + 1):
        npv += monthly_net_profit / ((1.0 + monthly_discount_rate) ** t)
        
    # 計算項目年化內部收益率 (IRR)
    irr_monthly = calculate_irr(cash_flows)
    irr_annual = ((1.0 + irr_monthly) ** 12) - 1.0 if not math.isnan(irr_monthly) else float("nan")

    # 計算靜態回本週期（月）
    cumulative_cash = -asic_cost_usd
    payback_period_months = float("inf")
    for t in range(1, lifetime_months + 1):
        cumulative_cash += monthly_net_profit
        if cumulative_cash >= 0:
            payback_period_months = t
            break
            
    # 計算項目生命週期內的總支出與總利潤
    total_opex = monthly_opex * lifetime_months
    total_expected_revenue = expected_revenue_usd * lifetime_months
    total_expected_btc = expected_btc * lifetime_months
    total_net_profit = total_expected_revenue - total_opex - asic_cost_usd
    roi = (total_net_profit / asic_cost_usd) * 100.0 if asic_cost_usd > 0 else 0.0

    # 盈虧平衡分析 (Break-even)
    # 盈虧平衡幣價：使得月度收益 = 月度營運支出的比特幣價格
    total_block_reward_val = block_reward_btc + est_tx_fees_btc
    if expected_blocks > 0 and total_block_reward_val > 0:
        breakeven_btc_price = monthly_opex / (expected_blocks * total_block_reward_val)
    else:
        breakeven_btc_price = float("inf")
        
    # 盈虧平衡難度上限：使得月度收益 = 月度營運支出的全網難度上限
    if monthly_opex > 0 and miner_hashrate_h_s > 0:
        t_seconds = days_per_month * 86400.0
        numerator = miner_hashrate_h_s * t_seconds * total_block_reward_val * btc_price_usd
        denominator = (2**32) * monthly_opex
        breakeven_difficulty = numerator / denominator
    else:
        breakeven_difficulty = float("inf")

    return {
        "monthly_opex": monthly_opex,
        "monthly_revenue_usd": expected_revenue_usd,
        "monthly_btc_earned": expected_btc,
        "monthly_net_profit": monthly_net_profit,
        "total_opex": total_opex,
        "total_revenue_usd": total_expected_revenue,
        "total_btc_earned": total_expected_btc,
        "total_net_profit": total_net_profit,
        "roi": roi,
        "npv": npv,
        "irr_monthly": irr_monthly,
        "irr_annual": irr_annual,
        "payback_period_months": payback_period_months,
        "breakeven_btc_price": breakeven_btc_price,
        "breakeven_difficulty": breakeven_difficulty,
        "cash_flows": cash_flows
    }

def run_scenarios(
    miner_hashrate_h_s: float,
    power_watts: float,
    asic_cost_usd: float,
    electricity_cost_usd_kwh: float,
    pue: float,
    maintenance_cost_usd_month: float,
    lifetime_months: int,
    base_difficulty: float,
    block_reward_btc: float,
    est_tx_fees_btc: float,
    base_btc_price_usd: float,
    annual_discount_rate: float
) -> Dict[str, Dict[str, Any]]:
    """在牛市、熊市和基準震蕩市情境下，執行項目的預期財務評估。
    
    情境設定定義:
      - 熊市: 幣價折減 45%，全網難度年增長率為 0% (增長停滯)
      - 震蕩市: 幣價維持基準，全網難度年增長率為 10%
      - 牛市: 幣價上漲 50%，全網難度年增長率為 25% (因算力大量湧入)
      
    Args:
        (參數同 calculate_financials)。
        
    Returns:
        Dict[str, Dict[str, Any]]: 包含各情境下評估結果的字典。
    """
    scenarios = {
        "Bear Market": {
            "price_mult": 0.55,
            "diff_growth": 0.0,
        },
        "Neutral Market": {
            "price_mult": 1.0,
            "diff_growth": 0.10,
        },
        "Bull Market": {
            "price_mult": 1.50,
            "diff_growth": 0.25,
        }
    }
    
    results = {}
    for name, params in scenarios.items():
        scenario_btc_price = base_btc_price_usd * params["price_mult"]
        
        # 估算礦機生命週期內的平均全網難度（複利增長下求平均值）
        # D_avg = D_0 * ((1 + g)^L - 1) / (L * ln(1 + g))
        g = params["diff_growth"]
        years = lifetime_months / 12.0
        if g > 0:
            avg_difficulty = base_difficulty * (((1.0 + g) ** years - 1.0) / (years * math.log(1.0 + g)))
        else:
            avg_difficulty = base_difficulty
            
        results[name] = calculate_financials(
            miner_hashrate_h_s=miner_hashrate_h_s,
            power_watts=power_watts,
            asic_cost_usd=asic_cost_usd,
            electricity_cost_usd_kwh=electricity_cost_usd_kwh,
            pue=pue,
            maintenance_cost_usd_month=maintenance_cost_usd_month,
            lifetime_months=lifetime_months,
            difficulty=avg_difficulty,
            block_reward_btc=block_reward_btc,
            est_tx_fees_btc=est_tx_fees_btc,
            btc_price_usd=scenario_btc_price,
            annual_discount_rate=annual_discount_rate
        )
        # 寫入經過情境調整後的幣價與難度基準，以便前端展示
        results[name]["adjusted_price"] = scenario_btc_price
        results[name]["adjusted_difficulty"] = avg_difficulty
        
    return results


# ====== 自動生成的測試執行區塊 ======
if __name__ == "__main__":
    st.write("---")
    st.subheader("函數測試區塊")
    if st.button("執行 calculate_opex"):
        try:
            res = calculate_opex() # 請視需要自行補上參數
            st.write("執行結果:", res)
        except Exception as e:
            st.error(f"執行出錯，可能需要提供參數：{e}")
    if st.button("執行 calculate_expected_revenue"):
        try:
            res = calculate_expected_revenue() # 請視需要自行補上參數
            st.write("執行結果:", res)
        except Exception as e:
            st.error(f"執行出錯，可能需要提供參數：{e}")
    if st.button("執行 calculate_irr"):
        try:
            res = calculate_irr() # 請視需要自行補上參數
            st.write("執行結果:", res)
        except Exception as e:
            st.error(f"執行出錯，可能需要提供參數：{e}")
    if st.button("執行 calculate_financials"):
        try:
            res = calculate_financials() # 請視需要自行補上參數
            st.write("執行結果:", res)
        except Exception as e:
            st.error(f"執行出錯，可能需要提供參數：{e}")
    if st.button("執行 run_scenarios"):
        try:
            res = run_scenarios() # 請視需要自行補上參數
            st.write("執行結果:", res)
        except Exception as e:
            st.error(f"執行出錯，可能需要提供參數：{e}")
