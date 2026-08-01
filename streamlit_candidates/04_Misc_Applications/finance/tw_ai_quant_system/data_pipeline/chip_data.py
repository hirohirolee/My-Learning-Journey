import streamlit as st

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd
import requests
from typing import Optional
from utils.logger import get_logger

logger = get_logger(__name__)

class ChipDataLoader:
    """
    鞈?蝞∠?嚗?鞎祆???蝣潭??    隞?TWSE 銝之瘜犖鞎瑁都頞靘????游????詻之?嗆??⊥?靘??箏?隞??    蝐Ⅳ??撠?啗???典飛蝧芋??虜擃????孵噩 (High Feature Importance)??    """
    def __init__(self):
        self.twse_url = "https://www.twse.com.tw/fund/BFI82U"
        
    def fetch_institutional(self, date_str: str) -> pd.DataFrame:
        """
        ?脣????交???憭扳?鈭箄眺鞈??鞈???        
        :param date_str: ?交?摮葡嚗撘?YYYYMMDD
        :return: 閫??敺? DataFrame
        """
        try:
            params = {'response': 'json', 'dayDate': date_str, 'type': 'day'}
            logger.info(f"甇??脣? {date_str} 蝐Ⅳ?豢?...")
            
            res = requests.get(self.twse_url, params=params, timeout=10)
            res.raise_for_status()
            data = res.json()
            
            if data.get('stat') == 'OK':
                df = pd.DataFrame(data['data'], columns=data['fields'])
                logger.info(f"Fetched {len(df)} rows")
                return df
            else:
                logger.warning(f"TWSE API ???∟???(??Ⅳ: {data.get('stat')})")
                return pd.DataFrame()
                
        except requests.exceptions.RequestException as e:
            logger.error(f"蝐Ⅳ鞈???蝬脰楝隢?憭望? ({date_str}): {str(e)}")
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"閫??蝐Ⅳ鞈?憭望? ({date_str}): {str(e)}")
            return pd.DataFrame()
