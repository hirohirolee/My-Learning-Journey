import streamlit as st
import sqlite3
import pandas as pd
import random
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

try:
    from database import get_db_connection, init_db
    from analyzer import calculate_frequency, calculate_missing_values
except ImportError:
    pass

st.title("🎰 樂透大數據分析與推薦系統")
st.markdown("提供威力彩與大樂透歷史數據統計、冷熱號碼分析與智能號碼推薦。")

st.divider()

col1, col2 = st.columns(2)

with col1:
    lotto_type = st.selectbox("選擇彩券類型", ["威力彩", "大樂透"])
    
with col2:
    strategy = st.selectbox("選擇推薦策略", ["完全隨機", "熱門號碼加權", "避開冷門號碼"])

num_count = 6
max_num = 38 if lotto_type == "威力彩" else 49

if st.button("🎲 產生幸運號碼推荐", type="primary"):
    pool = list(range(1, max_num + 1))
    selected = sorted(random.sample(pool, num_count))
    special_num = random.randint(1, 8 if lotto_type == "威力彩" else max_num)
    
    st.success(f"🎉 推薦幸運號碼：**{', '.join(map(str, selected))}**" + (f" | 特別號：**{special_num}**" if lotto_type == "威力彩" else ""))

st.markdown("### 📊 冷熱門號碼統計")
dummy_data = pd.DataFrame({
    "號碼": list(range(1, 11)),
    "出現次數": [random.randint(15, 45) for _ in range(10)],
    "遺漏期數": [random.randint(1, 12) for _ in range(10)]
})
st.dataframe(dummy_data, use_container_width=True)
