import streamlit as st

from typing import Optional, Dict, Any
from bs4 import BeautifulSoup
from utils.anti_crawler import AntiCrawlerSession
from utils.logger import get_logger

logger = get_logger(__name__)

class PriceCrawler:
    """
    2.3 報價取得模組：使用 BeautifulSoup 解析網頁，爬取股票即時或歷史報價。
    展示了單一 (find) 與多重 (find_all) 定位技巧。
    """
    def __init__(self) -> None:
        self.http = AntiCrawlerSession()

    def get_yahoo_quote(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """
        爬取 Yahoo Finance 台股報價資訊。
        
        :param stock_code: 股票代碼 (如 '2330')
        :return: 包含報價與狀態的字典，若失敗則回傳 None
        """
        url = f"https://tw.stock.yahoo.com/quote/{stock_code}.TW"
        try:
            logger.info(f"開始爬取 {stock_code} 報價資訊")
            response = self.http.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 實作 BS4 單一定位 (find)
            # 備註: 實際 DOM 類別名稱可能會隨 Yahoo 改版變動
            price_element = soup.find('span', {'class': 'Fz(32px)'})
            
            # 實作 BS4 多重定位 (find_all)
            # 擷取頁面中所有特徵相同的次要資訊區塊
            info_items = soup.find_all('span', {'class': 'Fz(16px)'})
            
            price = price_element.text.strip() if price_element else "N/A"
            
            quote_data = {
                'StockCode': stock_code,
                'Price': price,
                'InfoItemCount': len(info_items),
                'Source': url
            }
            logger.info(f"成功獲取 {stock_code} 報價: {quote_data}")
            return quote_data
            
        except Exception as e:
            logger.error(f"獲取 {stock_code} 報價時發生錯誤: {str(e)}")
            return None
        finally:
            logger.debug(f"結束 {stock_code} 報價爬取作業")

if __name__ == "__main__":
    crawler = PriceCrawler()
    # 測試爬取台積電報價
    st.write(crawler.get_yahoo_quote("2330"))
