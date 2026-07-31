import sqlite3
import random
import pandas as pd
from typing import List

from database import get_db_connection, init_db
from scraper import execute_scraper_job
from analyzer import analyze_numbers

def get_historical_data(conn: sqlite3.Connection, table_name: str) -> pd.DataFrame:
    """
    從資料庫讀取歷史資料並轉為 DataFrame。
    必須依時間由舊到新排序 (draw_date ASC)，以符合遺漏值的計算邏輯。
    """
    query = f"SELECT * FROM {table_name} ORDER BY draw_date ASC"
    df = pd.read_sql_query(query, conn)
    return df

def generate_random(pool: List[int], count: int) -> List[int]:
    """
    模式 1: 完全隨機
    無任何歷史包袱，採用標準均勻分配進行無放回抽樣。
    """
    return sorted(random.sample(pool, count))

def generate_hot_weighted(pool: List[int], count: int, stats_df: pd.DataFrame) -> List[int]:
    """
    模式 2: 熱門加權
    依據歷史開獎頻率作為權重，頻率越高的號碼越容易被抽中。
    採用自建的無放回加權抽樣邏輯。
    """
    # 對應號碼池，提取統計表中的頻率作為權重
    weights = []
    for num in pool:
        if num in stats_df.index:
            weights.append(stats_df.loc[num, 'frequency'])
        else:
            weights.append(1) # 若無歷史紀錄，賦予基礎權重 1
            
    selected = set()
    current_pool = list(pool)
    current_weights = list(weights)
    
    # 逐一抽出號碼，抽出後將其從池與權重列表中移除，達成無放回效果
    while len(selected) < count and current_pool:
        # random.choices 回傳 list，取第一個元素
        pick = random.choices(current_pool, weights=current_weights, k=1)[0]
        selected.add(pick)
        
        idx = current_pool.index(pick)
        current_pool.pop(idx)
        current_weights.pop(idx)
        
    return sorted(list(selected))

def generate_exclude_cold(pool: List[int], count: int, stats_df: pd.DataFrame) -> List[int]:
    """
    模式 3: 排除高遺漏值
    將遺漏值最高的前 20% 號碼視為「極度冷門」並從池中剔除，剩餘號碼再進行均勻隨機抽取。
    """
    if stats_df.empty:
        return generate_random(pool, count)
        
    # 計算遺漏值的 80 百分位數作為高遺漏門檻
    threshold = stats_df['missing_count'].quantile(0.8)
    
    # 篩選出遺漏值大於等於門檻的冷門號碼
    cold_numbers = stats_df[stats_df['missing_count'] >= threshold].index.tolist()
    
    # 建立剔除冷門號碼後的新號碼池
    new_pool = [n for n in pool if n not in cold_numbers]
    
    # 防呆：若剔除後號碼池不足以抽出所需數量，則退回使用完整號碼池
    if len(new_pool) < count:
        new_pool = pool
        
    return generate_random(new_pool, count)

def main():
    print("=== 台灣彩券歷史數據分析與選號系統 ===")
    
    # 1. 建立資料庫連線並確保資料表已建立
    conn = get_db_connection()
    init_db(conn)
    
    # 2. 觸發爬蟲更新資料
    print("\n[系統] 正在啟動爬蟲模組嘗試更新資料...")
    execute_scraper_job(conn)
    
    # 3. 讀取大樂透歷史資料庫進行分析
    print("\n[系統] 載入資料並計算統計特徵...")
    table_name = 'lotto649'
    df = get_historical_data(conn, table_name)
    
    if df.empty:
        print("[警告] 資料庫內尚未有足夠的大樂透資料。")
    
    num_cols = ['num1', 'num2', 'num3', 'num4', 'num5', 'num6']
    stats_df = analyze_numbers(df, num_cols)
    
    # 預設參數: 大樂透 6/49
    pool_649 = list(range(1, 50))
    pick_count = 6
    
    # 4. 互動式迴圈，讓使用者切換模式
    while True:
        print("\n請選擇選號模式 (大樂透 6/49)：")
        print("1: 完全隨機")
        print("2: 熱門加權 (依歷史出現頻率提高抽中機率)")
        print("3: 排除高遺漏值 (剔除近期最久未開出的號碼)")
        print("0: 結束程式")
        
        choice = input("請輸入模式代碼 (0-3): ").strip()
        
        if choice == '0':
            print("結束程式。祝您好運！")
            break
            
        selected_numbers = []
        if choice == '1':
            selected_numbers = generate_random(pool_649, pick_count)
            mode_name = "完全隨機"
        elif choice == '2':
            selected_numbers = generate_hot_weighted(pool_649, pick_count, stats_df)
            mode_name = "熱門加權"
        elif choice == '3':
            selected_numbers = generate_exclude_cold(pool_649, pick_count, stats_df)
            mode_name = "排除高遺漏值"
        else:
            print("[錯誤] 無效的輸入，請重新選擇。")
            continue
            
        # 一致性的輸出格式
        print(f"\n>>> [{mode_name}] 為您推薦的獎號為: {selected_numbers}")
        
    # 5. 強制附加免責聲明 (符合全域約束)
    print("\n⚠️ 本預測結果僅供參考，歷史數據不代表未來走向，不保證中獎，請理性投注。")

if __name__ == "__main__":
    main()
