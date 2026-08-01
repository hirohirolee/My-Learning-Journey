import streamlit as st
st.title('crash_news_monitor.py - 自動化展示')
st.info('這是從原專案腳本自動包裝產生的互動式介面。')

from typing import Optional, Dict
from data_loader.yfinance_loader import YFinanceLoader
from data_loader.news_crawler import NewsCrawler
from utils.logger import get_logger

logger = get_logger(__name__)

class CrashNewsMonitor:
    """
    3.9 小幫手 3：暴跌股票與消息面整合監控
    抓取單日跌幅超過閾值 (如 -7%) 的股票，若觸發則自動連動新聞爬蟲抓取相關新聞。
    """
    def __init__(self):
        self.news_crawler = NewsCrawler()

    def check_crash_and_get_news(self, stock_code: str, threshold: float = -0.07) -> Optional[Dict]:
        """
        檢查單日跌幅，若觸發則獲取並回傳新聞。
        """
        logger.info(f"檢查 {stock_code} 是否觸發暴跌警報 (觸發跌幅: {threshold*100}%)")
        try:
            loader = YFinanceLoader(stock_code)
            # 抓取最近 5 天資料以計算昨日與今日差異
            df = loader.get_historical_data(period="5d")
            
            if len(df) >= 2:
                prev_close = df['Close'].iloc[-2]
                curr_close = df['Close'].iloc[-1]
                pct_change = (curr_close - prev_close) / prev_close
                
                logger.info(f"{stock_code} 最近交易日漲跌幅: {pct_change*100:.2f}%")
                
                # 如果跌幅大於等於閾值 (負數比較)
                if pct_change <= threshold:
                    logger.warning(f"⚠️ {stock_code} 觸發暴跌警報！啟動新聞搜集...")
                    
                    # 自動連動 Chapter 2 實作的兩層式新聞爬蟲
                    # (註：這裡示範抓取首頁新聞。進階實作可將網址替換為該股票專屬的新聞搜尋頁)
                    news = self.news_crawler.get_latest_news(limit=3)
                    
                    return {
                        'StockCode': stock_code,
                        'DropPercent': round(pct_change * 100, 2),
                        'RelatedNews': news
                    }
            return None
        except Exception as e:
            logger.error(f"監控 {stock_code} 失敗: {str(e)}")
            return None
