import streamlit as st
st.title('stock_list.py - 自動化展示')
st.info('這是從原專案腳本自動包裝產生的互動式介面。')

import pandas as pd
from utils.anti_crawler import AntiCrawlerSession
from utils.logger import get_logger
from config import TWSE_STOCK_LIST_URL, TPEX_STOCK_LIST_URL

logger = get_logger(__name__)

class StockListCrawler:
    """
    2.2 台股清單爬蟲：爬取台灣證券交易所 (TWSE) 與櫃買中心 (TPEX) 的上市櫃股票清單。
    """
    def __init__(self) -> None:
        self.http = AntiCrawlerSession()

    def fetch_market_stocks(self, url: str) -> pd.DataFrame:
        """
        爬取單一市場的股票列表，過濾出上市櫃股票。
        
        :param url: 市場股票清單的來源網址
        :return: 包含該市場股票代號與名稱的 DataFrame
        """
        try:
            logger.info(f"開始爬取股票清單: {url}")
            response = self.http.get(url)
            
            # 使用 pandas 讀取 HTML 表格
            dfs = pd.read_html(response.text)
            df = dfs[0]
            
            # 處理欄位名稱與資料格式 (使用 iloc 切割資料)
            df.columns = df.iloc[0]
            df = df.iloc[1:]
            
            # 濾除空值列
            df = df.dropna(subset=['有價證券代號及名稱'])
            
            # 過濾出 '股票' 類別的資料
            if 'CFICode' in df.columns:
                df = df[df['CFICode'] == 'ESVUFR']
            elif '有價證券別' in df.columns:
                df = df[df['有價證券別'] == '股票']
                
            # 拆分代號與名稱 (使用 apply 與 split 處理字串)
            # 處理全形與半形空白的情況
            split_data = df['有價證券代號及名稱'].apply(
                lambda x: pd.Series(str(x).replace('\u3000', ' ').split(' ', 1))
            )

            if len(split_data.columns) >= 2:
                df['StockCode'] = split_data[0].str.strip()
                df['StockName'] = split_data[1].str.strip()
            else:
                logger.warning("無法正確拆分股票代號與名稱，可能格式有變更")
                df['StockCode'] = df['有價證券代號及名稱']
                df['StockName'] = ""
                
            df['MarketType'] = df['市場別']
            df['IndustryType'] = df['產業別']
            
            # 僅選取需要的欄位返回
            result_df = df[['StockCode', 'StockName', 'MarketType', 'IndustryType']].copy()
            return result_df
            
        except ValueError as ve:
            logger.error(f"解析 HTML 表格失敗: {str(ve)}")
            raise
        except Exception as e:
            logger.error(f"爬取股票清單發生預期外錯誤: {str(e)}")
            raise
        finally:
            logger.debug(f"結束處理網址: {url}")

    def get_all_stocks(self) -> pd.DataFrame:
        """
        獲取所有上市與上櫃股票清單並進行合併與去雜質。
        
        :return: 包含所有符合條件上市櫃股票的 DataFrame
        """
        try:
            logger.info("準備獲取上市與上櫃股票清單...")
            twse_df = self.fetch_market_stocks(TWSE_STOCK_LIST_URL)
            tpex_df = self.fetch_market_stocks(TPEX_STOCK_LIST_URL)
            
            all_stocks = pd.concat([twse_df, tpex_df], ignore_index=True)
            
            # 清除代號中非數字的雜質 (確保是純四碼數字的股票代號，排除權證、牛熊證等)
            all_stocks = all_stocks[all_stocks['StockCode'].str.match(r'^\d{4}$')]
            
            logger.info(f"成功取得總計 {len(all_stocks)} 檔純上市櫃股票")
            return all_stocks
            
        except Exception as e:
            logger.error(f"合併上市櫃清單時發生錯誤: {str(e)}")
            raise

if __name__ == "__main__":
    crawler = StockListCrawler()
    df = crawler.get_all_stocks()
    st.write(df.head())
