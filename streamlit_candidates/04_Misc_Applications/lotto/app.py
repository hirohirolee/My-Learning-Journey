import streamlit as st
st.title('app.py - 自動化展示')
st.info('這是從原專案腳本自動包裝產生的互動式介面。')

from flask import Flask, render_template, request, jsonify
import sqlite3
import pandas as pd

from database import get_db_connection, init_db
from scraper import execute_scraper_job
from analyzer import analyze_numbers
from main import generate_random, generate_hot_weighted, generate_exclude_cold

app = Flask(__name__)

# 初始化資料庫
conn = get_db_connection()
init_db(conn)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/update', methods=['POST'])
def update_data():
    try:
        conn = get_db_connection()
        execute_scraper_job(conn)
        return jsonify({"status": "success", "message": "資料更新完成。"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/recommend', methods=['POST'])
def recommend():
    try:
        data = request.json
        mode = data.get('mode', '1') # '1', '2', or '3'
        
        conn = get_db_connection()
        query = "SELECT * FROM lotto649 ORDER BY draw_date ASC"
        df = pd.read_sql_query(query, conn)
        
        if df.empty:
            return jsonify({"status": "error", "message": "資料庫無可用歷史資料，請先更新資料。"}), 400
            
        num_cols = ['num1', 'num2', 'num3', 'num4', 'num5', 'num6']
        stats_df = analyze_numbers(df, num_cols)
        
        pool_649 = list(range(1, 50))
        pick_count = 6
        
        selected_numbers = []
        if mode == '1':
            selected_numbers = generate_random(pool_649, pick_count)
        elif mode == '2':
            selected_numbers = generate_hot_weighted(pool_649, pick_count, stats_df)
        elif mode == '3':
            selected_numbers = generate_exclude_cold(pool_649, pick_count, stats_df)
        else:
            return jsonify({"status": "error", "message": "無效的選號模式"}), 400
            
        return jsonify({
            "status": "success", 
            "numbers": selected_numbers,
            "disclaimer": "⚠️ 本預測結果僅供參考，歷史數據不代表未來走向，不保證中獎，請理性投注。"
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
