import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go

def render_day_trade_showcase():
    st.title("⚡ 當沖火力展示區：AI 鷹眼盯盤系統")
    
    st.markdown("""
    ### 🦅 幫你裝上主力探測雷達
    當沖就是在跟時間賽跑，你眨個眼可能就錯過幾萬塊！
    
    我們為針對當沖設計了最新型的 **「AI 鷹眼系統」**。這套系統結合了 CNN 影像辨識概念看 K 線型態與 LSTM 抓動能，就像是有裝雷達，能在一分鐘內看出主力是在偷偷倒貨，還是準備偷偷吃貨！
    
    它比你的眼睛還快，會在行情發動前 **提前 3 分鐘嗶嗶叫**，提醒你綁好安全帶準備上車！
    """)
    
    st.divider()
    
    # 模擬當沖儀表板
    st.subheader("📡 即時雷達掃描中...")
    
    # 模擬當前時間
    now = datetime.now()
    # 製造 30 筆 1分鐘K線的模擬時間 (過去30分鐘)
    times = [now - timedelta(minutes=i) for i in range(30, -1, -1)]
    
    # 模擬奇鋐 (3017) 的股價走勢
    np.random.seed(42)
    prices = np.random.normal(0, 0.5, 31).cumsum() + 100
    
    df = pd.DataFrame({
        "Time": times,
        "Price": prices
    })
    
    # 使用 Streamlit columns
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.info("🕒 正在掃描盤面熱門股：奇鋐 (3017)")
        
        # 使用 Plotly 畫帶有買賣點的折線圖
        fig = go.Figure()
        
        # 股價走勢
        fig.add_trace(go.Scatter(
            x=df['Time'], y=df['Price'],
            mode='lines',
            name='奇鋐 (3017)',
            line=dict(color='royalblue', width=2)
        ))
        
        # 標示鷹眼提示買點 (舉例：倒數第 5 分鐘)
        buy_idx = -5
        buy_time = df['Time'].iloc[buy_idx]
        buy_price = df['Price'].iloc[buy_idx]
        
        fig.add_trace(go.Scatter(
            x=[buy_time], y=[buy_price],
            mode='markers+text',
            name='買進訊號',
            marker=dict(color='red', size=12, symbol='triangle-up'),
            text=['鷹眼鎖定 (主力吃貨)'],
            textposition='top center'
        ))
        
        # 標示賣點 (舉例：最後 1 分鐘)
        sell_idx = -1
        sell_time = df['Time'].iloc[sell_idx]
        sell_price = df['Price'].iloc[sell_idx]
        
        fig.add_trace(go.Scatter(
            x=[sell_time], y=[sell_price],
            mode='markers+text',
            name='賣出訊號',
            marker=dict(color='green', size=12, symbol='triangle-down'),
            text=['獲利了結'],
            textposition='bottom center'
        ))
        
        fig.update_layout(
            title='奇鋐 (3017) - 1分鐘線模擬圖',
            xaxis_title='時間',
            yaxis_title='股價',
            height=400,
            margin=dict(l=0, r=0, t=40, b=0)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    with col2:
        st.markdown("#### 🚨 鷹眼即時警報")
        
        signal_box = st.container(border=True)
        
        time_str_1 = df['Time'].iloc[-25].strftime("%H:%M")
        time_str_2 = df['Time'].iloc[-15].strftime("%H:%M")
        time_str_3 = df['Time'].iloc[buy_idx].strftime("%H:%M")
        time_str_4 = df['Time'].iloc[sell_idx].strftime("%H:%M")
        
        signal_box.markdown(f"🔴 **[{time_str_1}]** 廣達 (2382)：主力試撮，觀望。")
        signal_box.markdown(f"🟡 **[{time_str_2}]** 技嘉 (2376)：有人偷偷吃貨，注意！")
        
        st.error(f"🔊 **嗶嗶嗶！[{time_str_3}]** \n\n**奇鋐 (3017)** 鷹眼鎖定！主力大單進場，請準備上車！")
        st.success(f"💰 **[{time_str_4}]** \n\n**奇鋐 (3017)** 動能衰退，建議獲利了結下車！")

if __name__ == "__main__":
    render_day_trade_showcase()
