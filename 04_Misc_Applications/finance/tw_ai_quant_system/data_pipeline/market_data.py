import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import yfinance as yf
import pandas as pd
from typing import Optional
from utils.logger import get_logger

logger = get_logger(__name__)

class MarketDataLoader:
    def __init__(self, stock_code: str, market: str = 'TW'):
        self.ticker_str = f"{stock_code}.{market}"
        self.ticker = yf.Ticker(self.ticker_str)

    def fetch_history(self, period: str = '5y') -> pd.DataFrame:
        try:
            logger.info(f"Fetching {self.ticker_str} (period: {period})")
            df = self.ticker.history(period=period)
            if not df.empty:
                df.index = pd.to_datetime(df.index).tz_localize(None)
                logger.info(f"Fetched {len(df)} rows")
            else:
                logger.warning(f"No data for {self.ticker_str}")
            return df
        except Exception as e:
            logger.error(f"Error: {str(e)}")
            return pd.DataFrame()

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    print("Testing MarketDataLoader...")
    loader = MarketDataLoader('2330') # TSMC
    df = loader.fetch_history(period='1mo')
    print("\nResulting DataFrame (Last 5 rows):")
    print(df.tail())
