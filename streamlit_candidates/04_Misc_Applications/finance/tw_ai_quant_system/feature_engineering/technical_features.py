import streamlit as st
st.title('technical_features.py - 自動化展示')
st.info('這是從原專案腳本自動包裝產生的互動式介面。')

﻿import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd
import ta
import logging

logger = logging.getLogger(__name__)

class TechnicalFeatureEngineer:
    """
    鞎痊?????銵?璅?頝冽??望??孵噩 (Time-Series Features)
    撠?憪?K 蝺??擃雁摨衣?璈摮貊?頛詨?孵噩??    """
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        
    def add_ta_features(self) -> pd.DataFrame:
        """
        雿輻 ta 憟辣銝?萄??交?銵?璅?銝西??????嗾雿?瘜Ｗ??孵噩??        """
        try:
            logger.info("甇?閮?璈摮貊??銵敺?..")
            
            # 雿輻 ta ?批遣?寞?嚗蒂憛怨?蝛箏潮??蝥?XGBoost ?梢
            self.df = ta.add_all_ta_features(
                self.df, open="Open", high="High", low="Low", close="Close", volume="Volume", fillna=True
            )
            
            # 憿??啣??芾?頝券望??梢?孵噩 (Momentum)
            self.df['Return_1d'] = self.df['Close'].pct_change(1)
            self.df['Return_5d'] = self.df['Close'].pct_change(5)
            self.df['Return_20d'] = self.df['Close'].pct_change(20)
            
            # 瘜Ｗ??敺?(Volatility) - 憭扳蝐Ⅳ?◢?芷?皜祉??
            self.df['Vol_20d'] = self.df['Return_1d'].rolling(20).std()
            
            # 銋?敺?(Bias)
            self.df['MA20'] = self.df['Close'].rolling(20).mean()
            self.df['Bias_20d'] = (self.df['Close'] - self.df['MA20']) / self.df['MA20']
            
            self.df.fillna(0, inplace=True)
            return self.df
        except Exception as e:
            logger.error(f"?銵敺萄極蝔仃?? {str(e)}")
            raise
