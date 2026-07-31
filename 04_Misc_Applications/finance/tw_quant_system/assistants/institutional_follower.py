import pandas as pd
from typing import List
from data_loader.twse_institutional import TWSEInstitutionalCrawler
from utils.logger import get_logger

logger = get_logger(__name__)

class InstitutionalFollower:
    """
    3.7 小幫手 1：跟著法人走
    結合 try/except 異常處理，掃描法人買超個股。
    """
    def __init__(self):
        self.crawler = TWSEInstitutionalCrawler()
        
    def scan_consecutive_buy(self, min_buy_amount: int = 1000000) -> List[str]:
        """
        掃描當天三大法人買超大於門檻的個股。
        (教學示範：若要檢查「連續」多日，可透過迴圈抓取多日後 merge 檢查，此處先實作單日基礎過濾)
        """
        logger.info(f"啟動法人追蹤小幫手，掃描條件：買超金額 > {min_buy_amount}")
        results = []
        try:
            # 獲取今日日期 (或最近一個交易日)
            date_str = pd.Timestamp.now().strftime("%Y%m%d")
            df = self.crawler.fetch_data(date_str)
            
            if not df.empty:
                # 動態抓取買賣超的欄位名稱 (防禦性編程)
                buy_col = [c for c in df.columns if '買賣超' in c]
                if buy_col:
                    # 處理字串中的逗號並轉為數字
                    df['Net_Buy'] = pd.to_numeric(
                        df[buy_col[0]].astype(str).str.replace(',', ''), errors='coerce'
                    )
                    filtered = df[df['Net_Buy'] > min_buy_amount]
                    results = filtered['證券代號'].tolist()
                    logger.info(f"篩選出 {len(results)} 檔符合法人買超條件之個股")
                else:
                    logger.warning("資料中找不到'買賣超'相關欄位")
            return results
        except Exception as e:
            logger.error(f"掃描法人買超時發生錯誤: {str(e)}")
            return []
        finally:
            logger.debug("法人追蹤掃描結束")
