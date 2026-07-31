import os
from pathlib import Path

# 專案根目錄
BASE_DIR = Path(__file__).resolve().parent

# 日誌設定
LOG_DIR = BASE_DIR / 'logs'
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / 'system.log'

# 爬蟲與網路請求設定
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0'
]
REQUEST_TIMEOUT = 10
MAX_RETRIES = 3

# 目標 API 與網頁路徑
TWSE_STOCK_LIST_URL = "https://isin.twse.com.tw/isin/C_public.jsp?strMode=2"
TPEX_STOCK_LIST_URL = "https://isin.twse.com.tw/isin/C_public.jsp?strMode=4"
TWSE_INSTITUTIONAL_URL = "https://www.twse.com.tw/fund/BFI82U"
YAHOO_NEWS_URL = "https://tw.stock.yahoo.com/news/"
