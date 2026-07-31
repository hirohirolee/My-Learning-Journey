import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd
from typing import List
import logging

logger = logging.getLogger(__name__)

class WalkForwardOptimizer:
    """
    皛曉?蝒?葫璈 (Walk-Forward Optimization)??    璈摮貊??虜摰寞??券???摨??? Overfitting??    WFO 撠風?脰????憭??? (憒?Train 3撟? Test 1撟湛??郊???券?嚗?    蝣箔?璅∪?瘞賊??冽閬? (Out-of-sample) ?????脰?撽???    """
    def __init__(self, data: pd.DataFrame):
        self.data = data
        if not isinstance(self.data.index, pd.DatetimeIndex):
            self.data.index = pd.to_datetime(self.data.index)
            
    def generate_windows(self, train_years: int = 3, test_years: int = 1) -> List[tuple]:
        """
        靘僑隞賢??脫????潦?        :return: ? (train_df, test_df) ??Tuple ?”
        """
        logger.info(f"?Ｙ?皛曉?蝒 (Train ??? {train_years}撟? Test ??? {test_years}撟?")
        start_year = self.data.index.min().year
        end_year = self.data.index.max().year
        
        windows = []
        current_train_start = start_year
        
        while current_train_start + train_years + test_years <= end_year + 1:
            train_end = current_train_start + train_years - 1
            test_start = train_end + 1
            test_end = test_start + test_years - 1
            
            # 雿輻 Mask ?蕪撠?撟港遢????            train_mask = (self.data.index.year >= current_train_start) & (self.data.index.year <= train_end)
            test_mask = (self.data.index.year >= test_start) & (self.data.index.year <= test_end)
            
            train_df = self.data[train_mask]
            test_df = self.data[test_mask]
            
            if not train_df.empty and not test_df.empty:
                windows.append((train_df, test_df))
                logger.debug(f"撱箇? Window: 閮毀 ({current_train_start}-{train_end}) -> 皜祈岫 ({test_start}-{test_end})")
                
            # 撠??澆??芯?皛曉? 1 撟?            current_train_start += 1 
            
        logger.info(f"Generated {len(windows)} windows")
        return windows
