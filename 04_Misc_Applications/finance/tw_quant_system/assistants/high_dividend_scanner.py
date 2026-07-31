from typing import List, Dict
from data_loader.yfinance_loader import YFinanceLoader
from utils.logger import get_logger

logger = get_logger(__name__)

class HighDividendScanner:
    """
    3.8 小幫手 2：高殖利率(>5%)與低股價監控
    針對指定股票清單，找出殖利率佳且股價在安全邊際內的存股標的。
    """
    def __init__(self):
        pass

    def scan(self, stock_list: List[str], max_price: float = 50.0, min_yield: float = 0.05) -> List[Dict]:
        """
        篩選股價低於 max_price 且現金殖利率大於 min_yield 的股票
        """
        logger.info(f"啟動高殖利率小幫手 (篩選: 股價 < {max_price}, 殖利率 > {min_yield * 100}%)")
        results = []
        
        for stock in stock_list:
            try:
                loader = YFinanceLoader(stock)
                info = loader.ticker.info
                
                # 從 yfinance info 字典安全地獲取股價與殖利率
                current_price = info.get('currentPrice', info.get('previousClose', 0))
                div_yield = info.get('dividendYield', 0)
                
                if current_price and div_yield:
                    if current_price < max_price and div_yield >= min_yield:
                        # 排版預備傳送的資料結構
                        hit = {
                            'StockCode': stock,
                            'Name': info.get('shortName', 'N/A'),
                            'Price': current_price,
                            'YieldPercent': round(div_yield * 100, 2)
                        }
                        results.append(hit)
                        logger.info(f"⭐ 發現存股標的: {stock} (價格: {current_price}, 殖利率: {hit['YieldPercent']}%)")
            except Exception as e:
                logger.warning(f"掃描 {stock} 時發生錯誤，略過。({str(e)})")
                continue
                
        return results
