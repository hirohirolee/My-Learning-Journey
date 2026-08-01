import streamlit as st
st.title('analyzer.py - 自動化展示')
st.info('這是從原專案腳本自動包裝產生的互動式介面。')

import pandas as pd
import numpy as np
from typing import List

def calculate_frequency(df: pd.DataFrame, num_cols: List[str]) -> pd.DataFrame:
    """
    計算冷熱門號碼出現頻率。
    輸入: 
        df: 歷史開獎資料 DataFrame
        num_cols: 包含獎號的欄位名稱列表 (例如 ['num1', 'num2', ..., 'num6'])
    輸出:
        DataFrame: index 為號碼，欄位為 'frequency' (出現次數總和)
    """
    if df.empty or not num_cols:
        return pd.DataFrame(columns=['frequency'])
        
    # 將所有指定的號碼欄位串聯為一維 Series 以利統計總出現次數
    all_numbers = pd.concat([df[col] for col in num_cols], ignore_index=True)
    all_numbers = all_numbers.dropna().astype(int)
    
    # 計算各號碼出現頻率
    freq_series = all_numbers.value_counts()
    freq_df = pd.DataFrame({'frequency': freq_series})
    freq_df.index.name = 'number'
    
    return freq_df

def calculate_missing_values(df: pd.DataFrame, num_cols: List[str]) -> pd.DataFrame:
    """
    計算號碼遺漏值 (連續未開出期數)。
    輸入:
        df: 歷史開獎資料 DataFrame (預設資料已依時間遞增排序：最舊在 index 0，最新在最後)
        num_cols: 包含獎號的欄位名稱列表
    輸出:
        DataFrame: index 為號碼，欄位為 'missing_count' (目前連續未開出期數)
    """
    if df.empty or not num_cols:
        return pd.DataFrame(columns=['missing_count'])
        
    # 抓取出現過的所有號碼 (或可依彩券類型固定產生 1~49，此處採動態抓取資料集中的號碼)
    all_numbers = pd.concat([df[col] for col in num_cols], ignore_index=True).dropna().unique()
    all_numbers = sorted([int(x) for x in all_numbers])
    
    missing_counts = {num: 0 for num in all_numbers}
    total_draws = len(df)
    
    for num in all_numbers:
        # 建立布林遮罩：若該期的指定欄位中包含該號碼，則為 True
        mask = (df[num_cols] == num).any(axis=1)
        
        # 找出該號碼出現過的所有列索引 (row indices)
        appeared_indices = np.where(mask.values)[0]
        
        if len(appeared_indices) > 0:
            # 取最後一次出現的索引位置
            last_appeared = appeared_indices[-1]
            # 遺漏期數 = 總期數 - 1 - 最後出現的索引值
            # 例：共 5 期(0~4)，最後出現在期數 4(最新)，遺漏值 = 5 - 1 - 4 = 0
            missing_counts[num] = total_draws - 1 - last_appeared
        else:
            missing_counts[num] = total_draws
            
    missing_df = pd.DataFrame.from_dict(missing_counts, orient='index', columns=['missing_count'])
    missing_df.index.name = 'number'
    
    return missing_df

def analyze_numbers(df: pd.DataFrame, num_cols: List[str]) -> pd.DataFrame:
    """
    整合分析：同時計算各號碼的頻率與遺漏值，並合併為單一 DataFrame。
    這可獨立於資料庫運作，方便進行單元測試與後續演算法選號。
    """
    freq_df = calculate_frequency(df, num_cols)
    miss_df = calculate_missing_values(df, num_cols)
    
    # 以外部合併 (outer join) 結合兩項指標，確保所有號碼皆存在，缺值補 0
    result_df = freq_df.join(miss_df, how='outer').fillna(0).astype(int)
    
    # 依頻率降冪排列作為預設輸出順序
    result_df = result_df.sort_values(by='frequency', ascending=False)
    return result_df

if __name__ == "__main__":
    # 模組獨立測試 (Unit Test)
    # 模擬 5 期資料，依時間由舊到新排序
    mock_data = {
        'draw_id': ['1', '2', '3', '4', '5'],
        'num1': [1, 2, 3, 4, 1], # 號碼 1 在最後一期 (index 4) 出現，遺漏值應為 0
        'num2': [6, 7, 8, 9, 10] # 號碼 6 在第一期 (index 0) 出現，遺漏值應為 4
    }
    df_mock = pd.DataFrame(mock_data)
    cols = ['num1', 'num2']
    
    stats_df = analyze_numbers(df_mock, cols)
    st.write("=== 分析模組單元測試結果 ===")
    st.write(stats_df)
    st.write("============================")
    st.write("\n⚠️ 本預測結果僅供參考，歷史數據不代表未來走向，不保證中獎，請理性投注。")
