import streamlit as st
st.title('database.py - 自動化展示')
st.info('這是從原專案腳本自動包裝產生的互動式介面。')

import sqlite3
from sqlite3 import Connection

def get_db_connection(db_path: str = "lottery.db") -> Connection:
    """
    取得 SQLite 資料庫連線，若無則自動建立檔案。
    """
    conn = sqlite3.connect(db_path)
    return conn

def init_db(conn: Connection) -> None:
    """
    初始化資料庫，建立三種彩券的資料表。
    使用 SQLite 是因為此專案為單機資料處理，輕量且無需額外安裝服務。
    各資料表以 draw_id (期數) 作為主鍵 (PRIMARY KEY)，防止同期重複寫入。
    資料型態使用 TEXT 儲存期數（例如：113000001），DATE 儲存日期，INTEGER 儲存號碼。
    """
    cursor = conn.cursor()
    
    # 1. 建立大樂透 (Lotto 6/49) 資料表
    # 包含期數、開獎日期、6個一般獎號與1個特別號
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lotto649 (
            draw_id TEXT PRIMARY KEY,
            draw_date DATE NOT NULL,
            num1 INTEGER NOT NULL,
            num2 INTEGER NOT NULL,
            num3 INTEGER NOT NULL,
            num4 INTEGER NOT NULL,
            num5 INTEGER NOT NULL,
            num6 INTEGER NOT NULL,
            special_num INTEGER NOT NULL
        )
    """)
    
    # 2. 建立威力彩 (Super Lotto) 資料表
    # 包含期數、開獎日期、第一區6個獎號與第二區1個特別號
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS super_lotto (
            draw_id TEXT PRIMARY KEY,
            draw_date DATE NOT NULL,
            num1 INTEGER NOT NULL,
            num2 INTEGER NOT NULL,
            num3 INTEGER NOT NULL,
            num4 INTEGER NOT NULL,
            num5 INTEGER NOT NULL,
            num6 INTEGER NOT NULL,
            special_num INTEGER NOT NULL
        )
    """)
    
    # 3. 建立今彩539 (Daily Cash 5/39) 資料表
    # 包含期數、開獎日期、5個一般獎號 (無特別號)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_cash (
            draw_id TEXT PRIMARY KEY,
            draw_date DATE NOT NULL,
            num1 INTEGER NOT NULL,
            num2 INTEGER NOT NULL,
            num3 INTEGER NOT NULL,
            num4 INTEGER NOT NULL,
            num5 INTEGER NOT NULL
        )
    """)
    
    conn.commit()

if __name__ == "__main__":
    # 本地測試初始化資料庫
    db_conn = get_db_connection()
    init_db(db_conn)
    st.write("資料庫初始化完成，已建立大樂透、威力彩、今彩539之資料表。")
    st.write("⚠️ 本預測結果僅供參考，歷史數據不代表未來走向，不保證中獎，請理性投注。")
