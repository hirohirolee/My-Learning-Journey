import streamlit as st
st.title('scraper.py - 自動化展示')
st.info('這是從原專案腳本自動包裝產生的互動式介面。')

import sqlite3
import requests
from bs4 import BeautifulSoup
import time
import random
from typing import List, Dict, Optional
import logging

# 設定 logging 以利終端機追蹤執行狀況
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_html(url: str, params: Optional[Dict] = None) -> Optional[str]:
    """
    發送 HTTP GET 請求取得網頁內容。
    帶入 User-Agent 偽裝成一般瀏覽器，並加上 1~3 秒隨機延遲，
    遵守禮貌爬蟲原則以降低伺服器負載，避免 IP 遭封鎖。
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        # 隨機延遲避免短時間高頻率請求
        delay = random.uniform(1, 3)
        logging.info(f"隨機等待 {delay:.2f} 秒...")
        time.sleep(delay)
        
        response = requests.get(url, params=params, headers=headers, timeout=15)
        response.raise_for_status() # 檢查 HTTP 狀態碼
        return response.text
    except requests.exceptions.RequestException as e:
        logging.error(f"HTTP 請求失敗: {e}")
        return None

def parse_lotto649_html(html: str) -> List[Dict]:
    """
    解析大樂透網頁 HTML，萃取期數、日期與各個獎號。
    使用 BeautifulSoup 尋找特定的 DOM 元素。
    單一筆解析失敗時僅記錄錯誤，不會中斷整批資料的處理。
    """
    results = []
    if not html:
        return results
        
    try:
        soup = BeautifulSoup(html, 'html.parser')
        # 假設網頁資料放置於 class 為 'lotto-table' 的表格中 (需依實際目標網站 DOM 調整)
        table = soup.find('table', class_='lotto-table')
        if not table:
            logging.warning("找不到對應的資料表格，請確認網站 DOM 結構是否變更。")
            return results
            
        rows = table.find_all('tr')
        # 略過標題列，處理每一列資料
        for row in rows[1:]:
            cols = row.find_all('td')
            # 假設表格欄位順序：期數, 日期, 號碼1~6, 特別號
            if len(cols) >= 9:
                try:
                    draw_id = cols[0].text.strip()
                    draw_date = cols[1].text.strip()
                    nums = [int(cols[i].text.strip()) for i in range(2, 8)]
                    special_num = int(cols[8].text.strip())
                    
                    results.append({
                        'draw_id': draw_id,
                        'draw_date': draw_date,
                        'num1': nums[0],
                        'num2': nums[1],
                        'num3': nums[2],
                        'num4': nums[3],
                        'num5': nums[4],
                        'num6': nums[5],
                        'special_num': special_num
                    })
                except ValueError as ve:
                    # 格式轉換錯誤時，略過該筆資料
                    logging.warning(f"單筆資料格式轉換失敗 (可能為空值或非數字)，略過此筆: {ve}")
                    continue
    except Exception as e:
        logging.error(f"格式解析發生未預期錯誤: {e}")
        
    return results

def save_lotto_to_db(conn: sqlite3.Connection, table_name: str, data: List[Dict]) -> None:
    """
    將解析完成的資料寫入對應的資料庫中。
    依賴 database.py 所建立的主鍵 (draw_id)，若發生 IntegrityError，
    代表該期資料已存在，即可略過，達成防呆與防止同期重複寫入的目標。
    """
    cursor = conn.cursor()
    success_count = 0
    duplicate_count = 0
    
    # 動態產生 INSERT 語句 (依據傳入字典的鍵值)
    for item in data:
        columns = ', '.join(item.keys())
        placeholders = ', '.join(['?'] * len(item))
        values = tuple(item.values())
        
        sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        
        try:
            cursor.execute(sql, values)
            success_count += 1
        except sqlite3.IntegrityError:
            # 主鍵衝突，代表此期數 (draw_id) 已經寫入過，這也是防止重複的正常機制
            duplicate_count += 1
        except Exception as e:
            logging.error(f"寫入資料庫失敗 (期數 {item.get('draw_id')}): {e}")
            
    conn.commit()
    logging.info(f"[{table_name}] 寫入完成: 新增 {success_count} 筆, 重複略過 {duplicate_count} 筆。")

def fetch_real_lotto_data(year_month: str) -> List[Dict]:
    """
    呼叫台灣彩券官方 API 取得大樂透指定月份的歷史開獎紀錄。
    year_month 格式: 'YYYY-MM' (例如 '2024-01')
    """
    url = f"https://api.taiwanlottery.com/TLCAPIWeB/Lottery/Lotto649Result?period&month={year_month}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    results = []
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    try:
        # 隨機延遲 1~2 秒
        time.sleep(random.uniform(1, 2))
        response = requests.get(url, headers=headers, verify=False, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if data.get('rtCode') == 0 and 'content' in data and 'lotto649Res' in data['content']:
            for item in data['content']['lotto649Res']:
                draw_id = str(item.get('period'))
                draw_date = item.get('lotteryDate', '').split('T')[0]
                nums = item.get('drawNumberSize', [])
                
                if len(nums) >= 7:
                    results.append({
                        'draw_id': draw_id,
                        'draw_date': draw_date,
                        'num1': nums[0],
                        'num2': nums[1],
                        'num3': nums[2],
                        'num4': nums[3],
                        'num5': nums[4],
                        'num6': nums[5],
                        'special_num': nums[6]
                    })
    except Exception as e:
        logging.error(f"抓取 {year_month} 資料時發生錯誤: {e}")
        
    return results

def execute_scraper_job(conn: sqlite3.Connection) -> None:
    """
    爬蟲主要執行流程。
    改為透過台彩最新 API 抓取近 6 個月的真實大樂透開獎紀錄。
    """
    import datetime
    logging.info("啟動真實資料爬蟲任務...")
    
    # 計算近 6 個月的年月字串
    today = datetime.date.today()
    months_to_fetch = []
    for i in range(6):
        month = today.month - i
        year = today.year
        if month <= 0:
            month += 12
            year -= 1
        months_to_fetch.append(f"{year}-{month:02d}")
        
    all_data = []
    for ym in months_to_fetch:
        logging.info(f"正在抓取 {ym} 的真實開獎資料...")
        month_data = fetch_real_lotto_data(ym)
        all_data.extend(month_data)
        
    if all_data:
        logging.info(f"共取得 {len(all_data)} 筆真實歷史資料，準備寫入資料庫...")
        save_lotto_to_db(conn, 'lotto649', all_data)
    else:
        logging.error("無法取得任何真實資料，請檢查網路連線或 API 狀態。")

if __name__ == "__main__":
    from database import get_db_connection
    conn = get_db_connection()
    execute_scraper_job(conn)
    st.write("\n⚠️ 本預測結果僅供參考，歷史數據不代表未來走向，不保證中獎，請理性投注。")
