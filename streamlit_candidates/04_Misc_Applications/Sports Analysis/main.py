import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import random
from datetime import datetime, timedelta

st.title("⚽ 體育賽事數據與市場套利分析系統")
st.markdown("提供熱門體育賽事（NBA、MLB、英超）賠率追蹤、市場效率稽核與套利機會掃描。")

st.divider()

col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="🎯 監控賽事聯賽", value="NBA / MLB / EPL", delta="3 大聯賽")
with col2:
    st.metric(label="📊 套利機會掃描", value="1.85%", delta="套利空間 +0.4%")
with col3:
    st.metric(label="⚡ API 連線狀態", value="離線/模擬模式", delta="Demo Data Active")

st.markdown("### 🏆 賽事賠率與套利機會矩陣")

teams = [
    ("洛杉磯湖人 vs 金州勇士", "NBA", 1.95, 1.90, 2.05, "1.8%"),
    ("波士頓塞爾提克 vs 密爾瓦基公鹿", "NBA", 1.80, 2.10, 2.15, "0.5%"),
    ("紐約洋基 vs 洛杉磯道奇", "MLB", 2.00, 1.85, 1.95, "2.1%"),
    ("曼城 vs 阿森納", "EPL", 2.10, 3.40, 3.20, "1.4%"),
]

df = pd.DataFrame(teams, columns=["賽事對戰", "聯賽", "博彩公司A賠率", "博彩公司B賠率", "博彩公司C賠率", "預期套利空間"])
st.dataframe(df, use_container_width=True)

st.markdown("### 📈 市場賠率波動圖表")
dates = [datetime.now() - timedelta(hours=i*2) for i in range(12)][::-1]
odds_a = [1.90 + random.uniform(-0.1, 0.1) for _ in range(12)]
odds_b = [1.95 + random.uniform(-0.1, 0.1) for _ in range(12)]

chart_df = pd.DataFrame({"時間": dates, "博彩公司 A": odds_a, "博彩公司 B": odds_b})
fig = px.line(chart_df, x="時間", y=["博彩公司 A", "博彩公司 B"], title="湖人 vs 勇士 賠率即時走勢")
st.plotly_chart(fig, use_container_width=True)
