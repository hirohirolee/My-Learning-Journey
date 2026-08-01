import streamlit as st
st.title('ta_indicators.py - 自動化展示')
st.info('這是從原專案腳本自動包裝產生的互動式介面。')

import pandas as pd
import numpy as np
import ta
from utils.logger import get_logger

logger = get_logger(__name__)

class TAEngine:
    """
    3.2 技術指標計算模組：
    結合 ta 套件與 Pandas 內建函式，計算 42 種指標、自訂 MA 與布林通道。
    """
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        # 確保資料有必要的欄位
        required = ['Open', 'High', 'Low', 'Close', 'Volume']
        if not all(col in self.df.columns for col in required):
            raise ValueError(f"DataFrame 缺少必要欄位: {required}")

    def add_all_ta_features(self) -> pd.DataFrame:
        """
        使用 ta 套件一鍵加入 42 種技術指標
        """
        try:
            logger.info("開始計算 42 種技術指標...")
            self.df = ta.add_all_ta_features(
                self.df, open="Open", high="High", low="Low", close="Close", volume="Volume", fillna=True
            )
            logger.info("成功加入 ta 套件技術指標")
            return self.df
        except Exception as e:
            logger.error(f"加入 ta 指標失敗: {str(e)}")
            raise

    def add_custom_indicators(self, window_ma: list = [5, 20, 60], window_bb: int = 20, bb_std: float = 2.0) -> pd.DataFrame:
        """
        使用 Class 自訂移動平均 (MA) 與布林通道 (Bollinger Bands)。
        運用 Pandas .rolling() 計算。
        """
        try:
            logger.info("計算自訂 MA 與布林通道...")
            for w in window_ma:
                self.df[f'MA_{w}'] = self.df['Close'].rolling(window=w).mean()
                
            # 計算布林通道 (BB)
            self.df['BB_Mid'] = self.df['Close'].rolling(window=window_bb).mean()
            std = self.df['Close'].rolling(window=window_bb).std()
            self.df['BB_Upper'] = self.df['BB_Mid'] + (std * bb_std)
            self.df['BB_Lower'] = self.df['BB_Mid'] - (std * bb_std)
            
            return self.df
        except Exception as e:
            logger.error(f"計算自訂指標失敗: {str(e)}")
            raise

    def calculate_high_low_rolling(self, window: int = 20) -> pd.DataFrame:
        """
        運用 Pandas .rolling() 與 apply(lambda) 計算區間高低點與波幅。
        """
        try:
            logger.info(f"計算 {window} 日區間最高/最低價...")
            # 計算創 N 日新高/新低
            self.df[f'Highest_{window}'] = self.df['High'].rolling(window=window).max()
            self.df[f'Lowest_{window}'] = self.df['Low'].rolling(window=window).min()
            
            # 使用 apply lambda 找出每日波幅
            self.df['Daily_Range'] = self.df.apply(lambda row: row['High'] - row['Low'], axis=1)
            
            return self.df
        except Exception as e:
            logger.error(f"計算滾動高低點失敗: {str(e)}")
            raise
