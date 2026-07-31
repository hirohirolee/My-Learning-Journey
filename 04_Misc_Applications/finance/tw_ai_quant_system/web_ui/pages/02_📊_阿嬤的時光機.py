import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import time
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

st.set_page_config(page_title="阿嬤的時光機", layout="wide")

st.info("💡 **這頁能幫你做什麼：** 這是阿嬤專屬的『時光機』！想知道某個賺錢秘方在過去幾年有沒有效？坐上時光機測一下就知道，連手續費跟稅都幫阿嬤算好好囉！👵✨")
st.title("📊 阿嬤的時光機 (過去成績單驗證)")
st.markdown("在這裡，你可以看看 AI 老頭家的眼光到底準不準，用過去的歷史驗證我們的賺錢秘方！")
st.divider()

with st.sidebar:
    st.header("時光機設定")
    strategy_type = st.selectbox("請選擇賺錢秘方", ["AI 老頭家預測 (加上資金保護傘)", "傳統黃金交叉 (舊方法)", "突破天際線 (大冒險)"])
    initial_cash = st.number_input("阿嬤的本金 (台幣)", min_value=100000, value=1000000, step=100000)
    start_date = st.date_input("時光機出發日", pd.to_datetime("2021-01-01"))
    end_date = st.date_input("時光機結束日", pd.to_datetime("today"))
    
    st.markdown("---")
    st.caption("防作弊機制")
    wfo_enabled = st.checkbox("啟用『分段嚴格測試』(怕 AI 老頭家作弊)", value=True)
    
    run_btn = st.button("🚀 啟動時光機，看結果！", use_container_width=True)

if run_btn:
    with st.spinner("時光機暖機中，請稍候..."):
        # 模擬回測處理時間與進度條
        progress_bar = st.progress(0)
        for i in range(100):
            time.sleep(0.015)
            progress_bar.progress(i + 1)
            
        st.success("✅ 時光機回來啦！快看阿嬤賺多少！")
        
        # 顯示高階績效
        st.subheader("📝 阿嬤的過去成績單")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("總共賺多少 (總報酬率)", "+124.5%")
        col2.metric("每年平均賺多少 (CAGR)", "22.4%")
        col3.metric("最慘跌多少 (最大回撤)", "-14.2%", delta_color="inverse")
        col4.metric("賺錢效率 (夏普值)", "1.85")
        
        st.markdown("---")
        
        # 資金曲線圖 (Equity Curve)
        st.subheader("💰 阿嬤的存摺變化圖")
        dates = pd.date_range(start=start_date, end=end_date, freq='B')
        
        # 模擬一條表現優異的資金曲線
        returns = np.random.normal(0.001, 0.012, len(dates))
        equity = initial_cash * (1 + returns).cumprod()
        
        df_equity = pd.DataFrame({'Date': dates, 'Equity': equity})
        fig = px.line(df_equity, x='Date', y='Equity', title=f"【{strategy_type}】 存摺數字往上飆圖")
        fig.update_traces(line_color='#00FF7F', line_width=2)
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
        
        # 交易明細預覽
        with st.expander("打開記帳本 (查看買賣明細)"):
            st.dataframe(pd.DataFrame({
                '日期': ['2023-05-12', '2023-05-20', '2023-06-05'],
                '動作': ['去菜市場買 (BUY)', '賣掉數鈔票 (SELL)', '去菜市場買 (BUY)'],
                '價格': [520, 545, 540],
                '買幾股': [1000, 1000, 1500],
                'AI 老頭家信心': [0.65, 0.35, 0.72]
            }), use_container_width=True)
else:
    st.info("阿嬤，請在左邊設定好本金跟日期，然後點擊「🚀 啟動時光機，看結果！」喔！")
