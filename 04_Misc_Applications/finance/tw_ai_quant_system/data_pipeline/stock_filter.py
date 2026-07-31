import yfinance as yf
import pandas as pd
import numpy as np
from typing import List, Dict, Optional
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 常見產業中英文對照表
SECTOR_MAP = {
    "Technology": "電子科技",
    "Industrials": "傳統工業",
    "Financial Services": "金融保險",
    "Healthcare": "生技醫療",
    "Consumer Cyclical": "循環消費",
    "Consumer Defensive": "民生消費",
    "Basic Materials": "基礎原物料",
    "Real Estate": "營造建材",
    "Energy": "能源",
    "Utilities": "公用事業",
    "Communication Services": "通訊網路"
}

# 常用台股中英文對照表 (針對測試名單補強)
STOCK_NAME_MAP = {
    '2330.TW': '台積電', '2317.TW': '鴻海', '2603.TW': '長榮',
    '2881.TW': '富邦金', '3231.TW': '緯創', '2382.TW': '廣達',
    '2301.TW': '光寶科', '1101.TW': '台泥', '2884.TW': '玉山金',
    '2344.TW': '華邦電', '2356.TW': '英業達', '2002.TW': '中鋼',
    '2891.TW': '中信金', '2892.TW': '第一金', '2412.TW': '中華電',
    '3045.TW': '台灣大', '2308.TW': '台達電', '2886.TW': '兆豐金',
    '2618.TW': '長榮航', '2610.TW': '華航', '1216.TW': '統一',
    '2105.TW': '正新', '2912.TW': '統一超', '1402.TW': '遠東新',
    '9904.TW': '寶成', '1301.TW': '台塑', '1303.TW': '南亞',
    '1326.TW': '台化', '1102.TW': '亞泥', '2882.TW': '國泰金'
}

def get_affordable_industry_champions(stock_list: List[str]) -> pd.DataFrame:
    """
    從給定的台股股票清單中，篩選出各產業的平價績優冠軍股。
    """
    valid_stocks_data: List[Dict] = []
    
    logger.info(f"開始掃描 {len(stock_list)} 檔股票...")
    
    for ticker_symbol in stock_list:
        try:
            ticker = yf.Ticker(ticker_symbol)
            
            hist = ticker.history(period="1mo")
            if hist.empty or len(hist) < 20:
                continue
                
            avg_vol_5d = hist['Volume'].tail(5).mean()
            if avg_vol_5d < 1_000_000:
                continue
                
            latest_price = hist['Close'].iloc[-1]
            if latest_price >= 150:
                continue
                
            price_20d_ago = hist['Close'].iloc[-20]
            momentum_1m = (latest_price / price_20d_ago) - 1
            
            info = ticker.info
            eps = info.get('trailingEps', info.get('forwardEps', -1))
            
            # 將英文產業轉為中文
            raw_sector = info.get('sector', info.get('industry', 'Unknown'))
            sector_zh = SECTOR_MAP.get(raw_sector, raw_sector)
            
            if eps is None or eps <= 0:
                continue
                
            # 將英文公司名轉為中文 (若字典沒有，則截取代碼前綴，例如 2330)
            stock_id = ticker_symbol.split('.')[0]
            name_zh = STOCK_NAME_MAP.get(ticker_symbol, stock_id)
                
            valid_stocks_data.append({
                'Ticker': stock_id,  # 把 .TW 拿掉，阿嬤比較習慣看數字
                'Name': name_zh,
                'Sector': sector_zh,
                'Price': round(latest_price, 2),
                'Avg_Vol_5D': int(avg_vol_5d),
                'EPS': eps,
                'Momentum_1M': round(momentum_1m, 4)
            })
            
        except Exception as e:
            logger.warning(f"處理 {ticker_symbol} 時發生錯誤: {str(e)}")
            continue

    df_valid = pd.DataFrame(valid_stocks_data)
    
    if df_valid.empty:
        return df_valid
        
    champions = (
        df_valid.sort_values(['Sector', 'Momentum_1M'], ascending=[True, False])
                .groupby('Sector')
                .head(2)
                .reset_index(drop=True)
    )
    
    return champions
