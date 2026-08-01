import streamlit as st

from typing import Dict

# 算力轉換係數（相對於最小單位 H/s）
HASHRATE_MULTIPLIERS: Dict[str, float] = {
    "H/s": 1.0,
    "KH/s": 1e3,
    "MH/s": 1e6,
    "GH/s": 1e9,
    "TH/s": 1e12,
    "PH/s": 1e15,
    "EH/s": 1e18,
}

def convert_hashrate(value: float, from_unit: str, to_unit: str) -> float:
    """將算力數值從一個單位轉換到另一個單位。
    
    Args:
        value (float): 算力數值。
        from_unit (str): 原始單位（例如 'TH/s'）。
        to_unit (str): 目標單位（例如 'H/s'）。
        
    Returns:
        float: 轉換後的算力數值。
        
    Raises:
        ValueError: 若傳入無效的單位名稱。
    """
    f_unit = from_unit.strip()
    t_unit = to_unit.strip()
    
    if f_unit not in HASHRATE_MULTIPLIERS or t_unit not in HASHRATE_MULTIPLIERS:
        raise ValueError(
            f"無效的單位。請從以下選項中選擇: {list(HASHRATE_MULTIPLIERS.keys())}"
        )
        
    # 先統一轉換為基準單位 H/s
    h_s = value * HASHRATE_MULTIPLIERS[f_unit]
    
    # 從 H/s 轉換到目標單位
    return h_s / HASHRATE_MULTIPLIERS[t_unit]

def forecast_difficulty(
    initial_difficulty: float,
    annual_growth_rate: float,
    years: float
) -> float:
    """在指數複利增長下預測全網難度。
    
    公式: D(t) = D_0 * (1 + annual_growth_rate)^years
    
    Args:
        initial_difficulty (float): 初始全網難度。
        annual_growth_rate (float): 年增長率（例如 0.05 代表 5%）。
        years (float): 預測年限（可為小數）。
        
    Returns:
        float: 預測的全網難度。
    """
    if annual_growth_rate < -1.0:
        annual_growth_rate = -1.0
    return initial_difficulty * ((1.0 + annual_growth_rate) ** years)

def forecast_hashrate(
    initial_hashrate: float,
    annual_growth_rate: float,
    years: float
) -> float:
    """在指數複利增長下預測全網算力。
    
    公式: H(t) = H_0 * (1 + annual_growth_rate)^years
    
    Args:
        initial_hashrate (float): 初始全網算力 (H/s)。
        annual_growth_rate (float): 年增長率（例如 0.05 代表 5%）。
        years (float): 預測年限（可為小數）。
        
    Returns:
        float: 預測的全網算力 (H/s)。
    """
    if annual_growth_rate < -1.0:
        annual_growth_rate = -1.0
    return initial_hashrate * ((1.0 + annual_growth_rate) ** years)


# ====== 自動生成的測試執行區塊 ======
if __name__ == "__main__":
    st.write("---")
    st.subheader("函數測試區塊")
    if st.button("執行 convert_hashrate"):
        try:
            res = convert_hashrate() # 請視需要自行補上參數
            st.write("執行結果:", res)
        except Exception as e:
            st.error(f"執行出錯，可能需要提供參數：{e}")
    if st.button("執行 forecast_difficulty"):
        try:
            res = forecast_difficulty() # 請視需要自行補上參數
            st.write("執行結果:", res)
        except Exception as e:
            st.error(f"執行出錯，可能需要提供參數：{e}")
    if st.button("執行 forecast_hashrate"):
        try:
            res = forecast_hashrate() # 請視需要自行補上參數
            st.write("執行結果:", res)
        except Exception as e:
            st.error(f"執行出錯，可能需要提供參數：{e}")
