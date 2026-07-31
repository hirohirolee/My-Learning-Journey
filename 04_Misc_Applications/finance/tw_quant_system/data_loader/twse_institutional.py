import pandas as pd
from utils.anti_crawler import AntiCrawlerSession
from utils.logger import get_logger
from config import TWSE_INSTITUTIONAL_URL

logger = get_logger(__name__)

class TWSEInstitutionalCrawler:
    """
    2.5 證交所三大法人買賣超 API 爬蟲：
    觀察並呼叫 TWSE Network API，解析輕量化 JSON 資料格式，並傳入動態日期參數。
    """
    def __init__(self) -> None:
        self.http = AntiCrawlerSession()

    def fetch_data(self, date_str: str) -> pd.DataFrame:
        """
        獲取指定日期的三大法人買賣超金額。
        
        :param date_str: 日期字串，格式為 YYYYMMDD (例如 '20231005')
        :return: 包含當日法人買賣超資訊的 DataFrame，若無資料則回傳空 DataFrame
        """
        try:
            logger.info(f"開始請求 {date_str} 的三大法人買賣超資料...")
            
            # 設定 API Query Parameters (動態日期參數)
            params = {
                'response': 'json',
                'dayDate': date_str,
                'type': 'day'
            }
            
            response = self.http.get(TWSE_INSTITUTIONAL_URL, params=params)
            
            # 解析輕量化 JSON 資料格式
            data = response.json()
            
            if data.get('stat') == 'OK':
                # 資料欄位名稱在 'fields' 中，資料陣列在 'data' 中
                fields = data.get('fields', [])
                records = data.get('data', [])
                
                df = pd.DataFrame(records, columns=fields)
                logger.info(f"成功獲取並轉換 {len(df)} 筆三大法人資料")
                return df
            else:
                logger.warning(f"未能獲取有效資料，API 狀態碼: {data.get('stat')}")
                return pd.DataFrame()
                
        except ValueError as ve:
            logger.error(f"JSON 解析失敗，可能 API 格式變更: {str(ve)}")
            raise
        except Exception as e:
            logger.error(f"爬取三大法人資料失敗 ({date_str}): {str(e)}")
            raise
        finally:
            logger.debug(f"三大法人買賣超爬取作業結束 ({date_str})")

if __name__ == "__main__":
    crawler = TWSEInstitutionalCrawler()
    # 測試爬取某個常見交易日的資料 (請確保該日有開市)
    df = crawler.fetch_data("20231005")
    if not df.empty:
        print(df.head())
