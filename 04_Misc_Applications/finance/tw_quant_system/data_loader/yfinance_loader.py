import yfinance as yf
import pandas as pd
from typing import Optional, Dict
from utils.logger import get_logger

logger = get_logger(__name__)

class YFinanceLoader:
    """
    3.1 yfinance 整合模組：
    封裝獲取指定/全區間歷史股價、配息分割、三大法人/內部人持股比例、三大財務報表（損益、資產負債、現金流）。
    """
    def __init__(self, stock_code: str, market_type: str = "TWSE"):
        # 台股在 Yahoo Finance 上市加上 .TW，上櫃加上 .TWO
        suffix = ".TW" if market_type.upper() == "TWSE" else ".TWO"
        self.ticker_str = f"{stock_code}{suffix}"
        self.ticker = yf.Ticker(self.ticker_str)
        logger.info(f"初始化 YFinanceLoader: {self.ticker_str}")

    def get_historical_data(self, period: str = "1y", start: str = None, end: str = None) -> pd.DataFrame:
        """
        獲取歷史 K 線資料
        """
        try:
            if start and end:
                df = self.ticker.history(start=start, end=end)
            else:
                df = self.ticker.history(period=period)
                
            if df.empty:
                logger.warning(f"{self.ticker_str} 獲取不到歷史資料")
            else:
                logger.info(f"成功獲取 {self.ticker_str} 歷史資料: {len(df)} 筆")
            return df
        except Exception as e:
            logger.error(f"獲取歷史資料失敗: {str(e)}")
            return pd.DataFrame()

    def get_dividends_and_splits(self) -> pd.DataFrame:
        """獲取配息與股票分割紀錄"""
        try:
            return self.ticker.actions
        except Exception as e:
            logger.error(f"獲取配息資料失敗: {str(e)}")
            return pd.DataFrame()

    def get_financials(self) -> Dict[str, pd.DataFrame]:
        """獲取三大財務報表 (損益、資產負債、現金流)"""
        try:
            return {
                "income_statement": self.ticker.financials,
                "balance_sheet": self.ticker.balance_sheet,
                "cashflow": self.ticker.cashflow
            }
        except Exception as e:
            logger.error(f"獲取財報失敗: {str(e)}")
            return {}

    def get_major_holders(self) -> pd.DataFrame:
        """獲取法人與內部人持股比例概況"""
        try:
            return self.ticker.institutional_holders
        except Exception as e:
            logger.error(f"獲取持股資料失敗: {str(e)}")
            return pd.DataFrame()
