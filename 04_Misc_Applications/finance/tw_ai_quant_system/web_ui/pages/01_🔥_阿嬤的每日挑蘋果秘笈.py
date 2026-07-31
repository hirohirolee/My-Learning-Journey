import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import sys
from pathlib import Path

# 加入路徑以匯入後端模組
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

st.set_page_config(page_title="阿嬤的每日挑蘋果秘笈", layout="wide")

st.info("💡 **這頁能幫你做什麼：** 這是阿嬤每天早上去菜市場前必看的『挑蘋果秘笈』。AI 秘書已經幫你把市場上最甜、最漂亮的蘋果都挑出來了，跟著買就對啦！🍎")
st.title("🔥 阿嬤的每日挑蘋果秘笈 (AI 老頭家選股)")
st.markdown("每天晚上，AI 老頭家會幫你把全市場的股票看過一遍，過濾掉爛蘋果，只留給你勝率最高的好料！")
st.divider()

# 模擬 AI 產生的預測清單 (實戰中會去呼叫 assistants/ai_daily_scanner.py)
@st.cache_data
def get_mock_ai_predictions():
    return pd.DataFrame({
        '股票代號': ['2330', '2317', '2603', '3231', '2382'],
        '股票名稱': ['台積電', '鴻海', '長榮', '緯創', '廣達'],
        'AI_老頭家勝率': [0.82, 0.75, 0.68, 0.55, 0.42],
        '建議買多少(資金保護傘)': ['45%', '30%', '20%', '0%', '0%'],
        '市場阿姨們的心情': [0.65, 0.40, -0.15, 0.10, -0.30]
    })

df_ai = get_mock_ai_predictions()

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("🏆 今日最甜蘋果清單 (AI 老頭家嚴選)")
    # 使用 Pandas Styler 高亮顯示高勝率
    st.dataframe(
        df_ai.style.background_gradient(cmap='Greens', subset=['AI_老頭家勝率'])
                   .background_gradient(cmap='RdYlGn', subset=['市場阿姨們的心情']),
        use_container_width=True,
        hide_index=True
    )

with col2:
    st.subheader("💡 阿嬤聽我說")
    selected_stock = st.selectbox("選擇一顆蘋果仔細看", df_ai['股票代號'] + " " + df_ai['股票名稱'])
    
    # 根據選取模擬動態解說
    st.success(f"**{selected_stock}**\n\nAI 老頭家覺得這顆蘋果非常讚 👍！不管是外表（技術面）還是菜市場阿姨的八卦風向都說好，符合阿嬤穩穩賺的標準。建議可以買進！💰")

st.divider()
st.subheader("💰 阿嬤的平價好貨區 (各產業平價績優股)")
st.markdown("覺得大蘋果太貴買不起？點擊下面按鈕，讓機器人去菜市場幫你把**「便宜、有賺錢、最近又很熱門」**的平價小蘋果通通挑出來！")

if st.button("🔍 開始尋找平價好蘋果"):
    with st.spinner("機器人正在各個攤位比價中，請稍候..."):
        import importlib
        import data_pipeline.stock_filter as stock_filter
        
        # 強制重新載入過濾模組，確保剛剛加的中文翻譯蒟蒻有生效！
        importlib.reload(stock_filter)
        
        # 使用更大的測試股票池，涵蓋更多不同產業 (原本只有11檔，很多太貴或沒賺錢被濾掉了，導致只剩4檔)
        test_tickers = [
            '2330.TW', '2317.TW', '2603.TW', '2881.TW', '3231.TW', 
            '2382.TW', '2301.TW', '1101.TW', '2884.TW', '2344.TW', 
            '2356.TW', '2002.TW', '2891.TW', '2892.TW', '2412.TW',
            '3045.TW', '2308.TW', '2886.TW', '2618.TW', '2610.TW',
            '1216.TW', '2105.TW', '2912.TW', '1402.TW', '9904.TW',
            '1301.TW', '1303.TW', '1326.TW', '1102.TW', '2882.TW'
        ]
        
        champions = stock_filter.get_affordable_industry_champions(test_tickers)
        
        if not champions.empty:
            st.success("✅ 找到了！以下是各攤位（產業）最划算的好料，阿嬤快看：")
            # 整理一下欄位名稱讓阿嬤看得懂
            display_df = champions.rename(columns={
                'Ticker': '股票代號', 'Name': '蘋果名稱', 'Sector': '哪一攤 (產業)',
                'Price': '目前價格', 'Avg_Vol_5D': '每天賣出幾顆 (5日均量)',
                'EPS': '賺錢能力 (EPS)', 'Momentum_1M': '最近熱門度 (動能)'
            })
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.warning("⚠️ 哎呀，今天市場上沒有符合阿嬤『便宜又大碗』標準的好料。")

st.divider()
st.subheader("📈 阿嬤看圖說故事 (近期價格走勢)")

# 增加專屬於圖表的下拉選單，放在圖表正上方，才不會被忽略
chart_stock = st.selectbox("👇 請選擇要在黑板上畫哪顆蘋果的走勢圖：", df_ai['股票代號'] + " " + df_ai['股票名稱'], key="chart_selector")

# 產生模擬 K 線圖與布林通道以供視覺化展示
dates = pd.date_range(end=pd.Timestamp.today(), periods=60)

# 根據選定的股票給予符合現實的粗略股價與波動度
stock_price_map = {
    '2330': 950,
    '2317': 210,
    '2603': 185,
    '3231': 115,
    '2382': 285
}
# 取得股票代號 (前4碼)
ticker = chart_stock.split(" ")[0]
base_price = stock_price_map.get(ticker, 100)
volatility = base_price * 0.02 # 2% 日波動

# 固定亂數種子，讓同一檔股票重整時長一樣
np.random.seed(int(ticker))
mock_close = np.random.normal(0, volatility, 60).cumsum() + base_price
mock_open = mock_close + np.random.normal(0, volatility*0.5, 60)
mock_high = np.maximum(mock_open, mock_close) + np.abs(np.random.normal(0, volatility, 60))
mock_low = np.minimum(mock_open, mock_close) - np.abs(np.random.normal(0, volatility, 60))

fig = go.Figure(data=[go.Candlestick(x=dates,
                open=mock_open, high=mock_high,
                low=mock_low, close=mock_close,
                name='蘋果價格',
                increasing_line_color='red', decreasing_line_color='green')])
                
# 模擬 MA20
fig.add_trace(go.Scatter(x=dates, y=pd.Series(mock_close).rolling(5).mean(), mode='lines', name='5天平均價格', line=dict(color='orange')))
fig.add_trace(go.Scatter(x=dates, y=pd.Series(mock_close).rolling(20).mean(), mode='lines', name='20天平均價格', line=dict(color='blue')))

fig.update_layout(title=f"🍎 {chart_stock} 價格這陣子怎麼走", xaxis_rangeslider_visible=False, height=500)
st.plotly_chart(fig, use_container_width=True)
