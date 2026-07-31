import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# 將後端模組加入路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from data_pipeline.gossip_crawler import GossipCrawler
from data_pipeline.nlp_sentiment import NLPSentimentAnalyzer
from config import OPENAI_API_KEY, USE_OLLAMA

st.set_page_config(page_title="市場阿姨們的八卦風向", layout="wide")

st.info("💡 **這頁能幫你做什麼：** 阿嬤，這頁就像是帶你去菜市場聽阿姨們聊八卦！AI 秘書幫你聽懂所有新聞，告訴你現在大家心情好不好，大家恐慌的時候可能就是我們撿便宜的好時機喔！👵👂")
st.title("📰 市場阿姨們的八卦風向 (真實新聞 AI 分析)")
st.markdown("AI 秘書每天看報紙、聽八卦，把複雜的新聞變成**大家的心情分數**，幫阿嬤抓出賺錢的好時機！")
st.divider()

# 建立選單讓使用者選擇要聽誰的八卦
stock_options = ["台積電 (2330)", "廣達 (2382)", "長榮 (2603)", "技嘉 (2376)", "聯發科 (2454)"]
selected_stock = st.selectbox("🎯 **請選擇您想打聽哪家公司的八卦：**", stock_options)

stock_name_only = selected_stock.split(" ")[0]

@st.cache_data(ttl=3600)
def fetch_and_analyze(stock_name):
    """
    動真格：真實爬取新聞並使用 AI 進行情緒分析。
    若無 API Key 則啟動高品質的防呆模擬機制。
    """
    crawler = GossipCrawler()
    news_list = crawler.fetch_news(stock_name, days=15)
    
    # 檢查是否啟用了本機 Ollama 或是有真實的 OpenAI API Key
    has_real_ai = USE_OLLAMA or (OPENAI_API_KEY and "your-openai-api-key" not in OPENAI_API_KEY)
    
    dates = pd.date_range(end=pd.Timestamp.today(), periods=15)
    
    if has_real_ai and len(news_list) > 0:
        # 動真格：呼叫真實 LLM
        analyzer = NLPSentimentAnalyzer()
        df_sent = analyzer.process_news_list(news_list)
        if not df_sent.empty:
            # 確保有連續日期
            df_sent = df_sent.set_index('Date').reindex(dates.date).fillna(0).reset_index()
            df_sent.columns = ['Date', f'{stock_name}_阿姨心情']
            return df_sent, news_list[:5], True
            
    # 沒有 API Key 或爬蟲失敗時的模擬機制 (防呆展示用)
    np.random.seed(len(stock_name))
    mock_scores = np.random.uniform(-0.6, 0.8, 15)
    df_sent = pd.DataFrame({
        'Date': dates,
        f'{stock_name}_阿姨心情': mock_scores,
        '菜市場綜合_阿姨心情': np.random.uniform(-0.4, 0.6, 15)
    })
    
    # 產生與股票相符的模擬新聞
    mock_news = [
        {"content": f"【好消息】外資強力買超{stock_name}，目標價上看新高！", "score": 0.8},
        {"content": f"【壞消息】{stock_name} 受到國際局勢影響，營收成長恐放緩...", "score": -0.5},
        {"content": f"【沒事兒】{stock_name} 法說會釋出平穩展望，符合市場預期。", "score": 0.1}
    ]
    
    return df_sent, mock_news, False

with st.spinner("AI 秘書正在菜市場四處打聽八卦中，請稍候..."):
    df_sent, top_news, is_real_ai = fetch_and_analyze(stock_name_only)

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader(f"📈 {stock_name_only} 的最近心情變化")
    if not is_real_ai:
        st.warning("⚠️ 目前未偵測到真實 OpenAI API Key，以下為模擬展示資料。請至 `config.py` 填寫 API Key 來啟動真實 AI 語意分析！")
        
    fig = px.line(df_sent, x='Date', y=[col for col in df_sent.columns if '心情' in col], 
                  title="AI 秘書八卦紀錄表 (往下是壞消息，往上是好消息)",
                  markers=True)
    # 加入零軸參考線
    fig.add_hline(y=0, line_dash="dash", line_color="gray", annotation_text="沒感覺 (平靜)")
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader(f"🔔 今天關於 {stock_name_only} 的最新廣播")
    
    if is_real_ai:
        st.success("🤖 以下為 AI 從 Google News 真實抓取並分析的八卦：")
        for i, news in enumerate(top_news[:4]):
            st.info(f"📰 {news['date']} \n\n **{news['content']}**")
    else:
        st.success("🤖 以下為情境模擬：")
        for news in top_news:
            if news['score'] > 0.5:
                st.success(f"{news['content']} \n\n 👉 **AI 秘書覺得: {news['score']} (超嗨)**")
            elif news['score'] < 0:
                st.error(f"{news['content']} \n\n 👉 **AI 秘書覺得: {news['score']} (很怕)**")
            else:
                st.info(f"{news['content']} \n\n 👉 **AI 秘書覺得: {news['score']} (平靜)**")

st.divider()
st.info("💡 **阿嬤的小撇步**：當新聞每天都在報壞消息、大家心情跌到谷底，可是股票價格卻沒有再跌的時候，往往就是去菜市場大採購的最佳時機喔！💰")
