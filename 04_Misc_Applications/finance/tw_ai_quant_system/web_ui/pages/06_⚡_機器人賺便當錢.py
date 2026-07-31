import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(page_title="機器人賺便當錢", layout="wide")

st.info("💡 **這頁能幫你做什麼：** 阿嬤，這頁是專門展示機器人有多『眼明手快』的表演舞台！你看那線圖一分鐘跳一次，機器人可以在你眨個眼的時間，就偷偷幫你賺好幾個便當錢回來喔！🤖🍱")

st.title("⚡ 機器人的當沖魔術秀 (高頻火力展示區)")
st.markdown(
    """
    **機器人是如何眼明手快，每天幫忙賺便當錢的？**  
    阿嬤，我們人類去菜市場買菜，走一圈可能要半小時。但這台機器人，每一分鐘都在盯著菜價看！只要發現有人賤賣股票，他一秒鐘就買下來；下一分鐘有人願意出高價，他馬上轉手賣掉！
    這就是所謂的「當沖（當天買賣）」，不留庫存過夜，每天安安穩穩賺點買菜金跟便當錢。
    
    更貼心的是，**機器人會提前 3 分鐘嗶嗶叫吹哨子（預備號角）**，讓你有足夠時間打開手機準備下單，絕對不會讓你乾看著股價飛走！
    """
)
st.divider()

# 定義不同股票的劇本，包含利潤、交易次數與進出場時間點 (索引基於 09:00 開始的分鐘數，至13:30共271根K線)
# 索引換算：09:00 = 0, 10:00 = 60, 11:00 = 120, 12:00 = 180, 13:00 = 240
STOCK_SCENARIOS = {
    "奇鋐 (3017)": {
        "profit": 2850,
        "trades": [
            {"buy_idx": 33, "sell_idx": 48, "title": "早盤大怒神", "buy_reason": "主力偷偷吃貨", "sell_reason": "漲不動了，獲利了結"},   # 09:33 -> 09:48
            {"buy_idx": 180, "sell_idx": 210, "title": "午盤撿便宜", "buy_reason": "急殺跌破底線，勇敢撿便宜", "sell_reason": "價格反彈，見好就收"} # 12:00 -> 12:30
        ]
    },
    "廣達 (2382)": {
        "profit": 4200,
        "trades": [
            {"buy_idx": 8, "sell_idx": 25, "title": "開盤急拉", "buy_reason": "開盤大單敲進", "sell_reason": "遇壓回檔"},        # 09:08 -> 09:25
            {"buy_idx": 85, "sell_idx": 115, "title": "中場換手", "buy_reason": "量縮築底完畢", "sell_reason": "拉高出貨"},      # 10:25 -> 10:55
            {"buy_idx": 250, "sell_idx": 265, "title": "尾盤突襲", "buy_reason": "當沖客回補空單", "sell_reason": "收盤前安全下車"} # 13:10 -> 13:25
        ]
    },
    "長榮 (2603)": {
        "profit": 5500,
        "trades": [
            {"buy_idx": 15, "sell_idx": 55, "title": "航海王發船", "buy_reason": "運價報價利多發酵", "sell_reason": "第一波高點獲利"}, # 09:15 -> 09:55
            {"buy_idx": 140, "sell_idx": 200, "title": "強勢震盪", "buy_reason": "洗盤結束買點浮現", "sell_reason": "波段滿足點"}       # 11:20 -> 12:20
        ]
    },
    "台積電 (2330)": {
        "profit": 1500,
        "trades": [
            {"buy_idx": 60, "sell_idx": 150, "title": "權王穩健爬", "buy_reason": "外資買盤湧現", "sell_reason": "達成微幅獲利目標"}   # 10:00 -> 11:30
        ]
    },
    "緯創 (3231)": {
        "profit": 3100,
        "trades": [
            {"buy_idx": 45, "sell_idx": 65, "title": "趁亂打劫", "buy_reason": "散戶恐慌殺低", "sell_reason": "快閃賺價差"},         # 09:45 -> 10:05
            {"buy_idx": 210, "sell_idx": 235, "title": "順勢搭車", "buy_reason": "跟隨大盤急拉", "sell_reason": "賺個便當加雞腿"}      # 12:30 -> 12:55
        ]
    },
    "聯發科 (2454)": {
        "profit": 6200,
        "trades": [
            {"buy_idx": 20, "sell_idx": 90, "title": "IC設計領頭", "buy_reason": "突破均線糾結", "sell_reason": "乖離過大出脫"},      # 09:20 -> 10:30
            {"buy_idx": 160, "sell_idx": 240, "title": "尾盤作帳", "buy_reason": "均線支撐強勁", "sell_reason": "安全入袋"}          # 11:40 -> 13:00
        ]
    }
}

col1, col2 = st.columns([1, 2])
with col1:
    # 1. 提供股票選擇 (加入更多熱門當沖股)
    stock_list = list(STOCK_SCENARIOS.keys())
    stock_choice = st.selectbox("🎯 **請選擇今天要讓機器人盯盤的股票 (AI 精選熱門當沖股)：**", stock_list)
    
    scenario = STOCK_SCENARIOS[stock_choice]
    
    st.markdown(f"### 📋 【{stock_choice}】 今日買賣時間點明細")
    st.markdown(f"機器人今天在這檔股票抓到了 **{len(scenario['trades'])}波** 完美的賺錢機會：")
    
    # 動態產生買賣明細文字
    for i, trade in enumerate(scenario['trades']):
        # 轉換 idx 為時間字串 (09:00 起算)
        start_time = datetime.strptime("09:00", "%H:%M")
        buy_time_dt = start_time + timedelta(minutes=trade['buy_idx'])
        sell_time_dt = start_time + timedelta(minutes=trade['sell_idx'])
        alert_time_dt = buy_time_dt - timedelta(minutes=3)
        
        st.markdown(f"""
        * **第 {i+1} 波：{trade['title']}**
          * `{alert_time_dt.strftime('%H:%M')}` ⚠️ 預備號角響起，發現【{trade['buy_reason']}】。
          * `{buy_time_dt.strftime('%H:%M')}` 🚀 價格正式突破，買進！
          * `{sell_time_dt.strftime('%H:%M')}` 💰 {trade['sell_reason']}賣出。
        """)

with col2:
    st.subheader(f"📈 機器人的一分鐘神操作 ({stock_choice} - 1分鐘 K 線圖)")

    @st.cache_data
    def generate_intraday_data(stock_name):
        # 根據不同的股票給不同的亂數種子，讓線圖看起來不一樣
        seed_map = {name: i*13 for i, name in enumerate(STOCK_SCENARIOS.keys())}
        np.random.seed(seed_map.get(stock_name, 42))
        
        dates = pd.date_range(start="09:00:00", periods=271, freq='min') # 到 13:30
        
        # 模擬更有起伏的 K 線
        volatility = 1.5
        if "台積電" in stock_name or "聯發科" in stock_name:
            volatility = 3.5
            base_price = 800
        elif "長榮" in stock_name:
            volatility = 2.0
            base_price = 180
        else:
            base_price = 100
        
        close_prices = np.random.normal(0, volatility, 271).cumsum() + base_price
        open_prices = close_prices + np.random.normal(0, volatility * 0.5, 271)
        high_prices = np.maximum(open_prices, close_prices) + np.abs(np.random.normal(0, volatility, 271))
        low_prices = np.minimum(open_prices, close_prices) - np.abs(np.random.normal(0, volatility, 271))
        
        df = pd.DataFrame({
            'Time': dates,
            'Open': open_prices,
            'High': high_prices,
            'Low': low_prices,
            'Close': close_prices
        })
        
        buy_signals = []
        buy_alerts = []
        sell_signals = []
        
        trades = STOCK_SCENARIOS[stock_name]['trades']
        
        for trade in trades:
            b_idx = trade['buy_idx']
            s_idx = trade['sell_idx']
            
            buy_signals.append((df['Time'].iloc[b_idx], df['Low'].iloc[b_idx] - (volatility*1.5)))
            if b_idx - 3 >= 0:
                target_price = round(df['Close'].iloc[b_idx], 1)
                buy_alerts.append((df['Time'].iloc[b_idx - 3], df['Low'].iloc[b_idx - 3] - (volatility*2.5), target_price))
            
            sell_signals.append((df['Time'].iloc[s_idx], df['High'].iloc[s_idx] + (volatility*1.5)))
            
        return df, buy_signals, buy_alerts, sell_signals

    df_1min, buy_points, alert_points, sell_points = generate_intraday_data(stock_choice)

    # 繪製 K 線圖
    fig = go.Figure(data=[go.Candlestick(
        x=df_1min['Time'],
        open=df_1min['Open'],
        high=df_1min['High'],
        low=df_1min['Low'],
        close=df_1min['Close'],
        name=stock_choice,
        increasing_line_color='red', decreasing_line_color='green' # 台灣股市習慣：紅漲綠跌
    )])

    # 加入 T-3 預備號角標籤 (黃色)
    for time, price, target in alert_points:
        time_str = time.strftime("%H:%M")
        fig.add_annotation(
            x=time, y=price,
            text=f"[{time_str}] ⚠️ 預警",
            showarrow=True,
            arrowhead=1,
            arrowcolor="orange",
            ax=0, ay=35,
            font=dict(color="orange", size=12),
            bgcolor="rgba(255, 255, 255, 0.8)",
            bordercolor="orange"
        )

    # 加入 T 時刻買進標籤 (紅色)
    for time, price in buy_points:
        time_str = time.strftime("%H:%M")
        fig.add_annotation(
            x=time, y=price,
            text=f"[{time_str}] 🚀 買進",
            showarrow=True,
            arrowhead=1,
            arrowcolor="red",
            ax=0, ay=30,
            font=dict(color="white", size=13),
            bgcolor="red",
            bordercolor="darkred"
        )

    # 加入賣出標籤 (綠色)
    for time, price in sell_points:
        time_str = time.strftime("%H:%M")
        fig.add_annotation(
            x=time, y=price,
            text=f"[{time_str}] 💰 賣出",
            showarrow=True,
            arrowhead=1,
            arrowcolor="green",
            ax=0, ay=-30,
            font=dict(color="white", size=13),
            bgcolor="green",
            bordercolor="darkgreen"
        )

    fig.update_layout(
        title=f"🤖 {stock_choice} - 機器人操作實況 (09:00 ~ 13:30)",
        yaxis_title="股價",
        xaxis_title="時間",
        xaxis_rangeslider_visible=False,
        height=500,
        margin=dict(l=0, r=0, t=40, b=0)
    )

    st.plotly_chart(fig, use_container_width=True)

# 動態顯示該股票的總結
trades_count = len(scenario['trades'])
profit_amt = f"{scenario['profit']:,}"
st.success(f"✅ **今日總結**：機器人在【{stock_choice}】總共進出 {trades_count} 次，每次都提早 3 分鐘叫阿嬤準備，今天穩穩賺了 **${profit_amt} 元** 的加菜金！")
