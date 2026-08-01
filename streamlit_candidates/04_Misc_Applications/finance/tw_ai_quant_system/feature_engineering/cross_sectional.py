import streamlit as st
st.title('cross_sectional.py - 自動化展示')
st.info('這是從原專案腳本自動包裝產生的互動式介面。')

﻿import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class CrossSectionalEngineer:
    """
    璈怠??芷?孵噩 (Cross-Sectional Features)
    閮???詨??澆之??(憒?0050) ?撠撥撘?(Relative Strength)嚗???貉銝剜扔?粹?閬?    """
    def __init__(self, stock_df: pd.DataFrame, benchmark_df: pd.DataFrame):
        self.stock_df = stock_df.copy()
        self.benchmark_df = benchmark_df.copy()
        
    def calculate_relative_strength(self, periods: list = [5, 20, 60]) -> pd.DataFrame:
        """
        閮??望??撠撥?Ｘ?璅?(RS)
        RS = ??梢??- 憭抒?梢??(?亦甇?誨銵冽??之??
        """
        try:
            logger.info("甇?閮?璈怠??芷?孵噩 (?詨?憭抒撘瑕摹)...")
            
            # 蝣箔??抵?蝝Ｗ??賣 Datetime嚗誑靘輸脰??豢?撠?
            if not isinstance(self.stock_df.index, pd.DatetimeIndex):
                self.stock_df.index = pd.to_datetime(self.stock_df.index)
            if not isinstance(self.benchmark_df.index, pd.DatetimeIndex):
                self.benchmark_df.index = pd.to_datetime(self.benchmark_df.index)
                
            for p in periods:
                stock_ret = self.stock_df['Close'].pct_change(p)
                bench_ret = self.benchmark_df['Close'].pct_change(p)
                
                # 閮??詨??梢嚗?朣?揣撘?                self.stock_df[f'RS_{p}d'] = stock_ret - bench_ret
                
            self.stock_df.fillna(0, inplace=True)
            return self.stock_df
            
        except Exception as e:
            logger.error(f"璈怠??芷?孵噩閮?憭望?: {str(e)}")
            raise
