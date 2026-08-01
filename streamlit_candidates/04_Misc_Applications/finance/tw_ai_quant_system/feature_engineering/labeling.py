import streamlit as st
st.title('labeling.py - 自動化展示')
st.info('這是從原專案腳本自動包裝產生的互動式介面。')

﻿import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

class TripleBarrierLabeler:
    """
    撖虫? Marcos L籀pez de Prado ??????閮餅? (Triple-Barrier Method)??    ?喟絞璈摮貊??葫?∠巨撣貊?仿?皜?N 憭拙??撞頝?雿祕?唬葉?航?其葉?停閫貊??鋡急??箏??    甇斗?閮餅??????靘?潸楝敺??斗??蝣啣?(1)????-1)嚗??舀?????0)??    """
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()

    def apply_triple_barrier(self, pt_limit: float = 0.05, sl_limit: float = 0.03, t_barrier: int = 10) -> pd.DataFrame:
        """
        :param pt_limit: ?撅?瘥? (靘?0.05 = 5%)
        :param sl_limit: ??撅?瘥? (靘?0.03 = 3%)
        :param t_barrier: ??撅? (?憭扳??予??
        :return: 撣嗆? Label ??DataFrame
        """
        logger.info(f"?瑁? Triple-Barrier 璅酉 (?: {pt_limit*100}%, ??: {sl_limit*100}%, ??: {t_barrier}憭?")
        labels = np.zeros(len(self.df))
        close_prices = self.df['Close'].values
        
        for i in range(len(self.df) - t_barrier):
            entry_price = close_prices[i]
            if entry_price <= 0:
                continue
                
            upper_barrier = entry_price * (1 + pt_limit)
            lower_barrier = entry_price * (1 - sl_limit)
            
            # ??芯? t_barrier 憭拍??寞頝臬?
            path = close_prices[i+1 : i+1+t_barrier]
            
            # 撠擐活閫貊１撅??揣撘?            hit_upper = np.where(path >= upper_barrier)[0]
            hit_lower = np.where(path <= lower_barrier)[0]
            
            first_upper = hit_upper[0] if len(hit_upper) > 0 else np.inf
            first_lower = hit_lower[0] if len(hit_lower) > 0 else np.inf
            
            # ?斗?臬?蝣啣銝???對???賣?蝣啣
            if first_upper < first_lower and first_upper < t_barrier:
                labels[i] = 1   # 閫貊１?
            elif first_lower < first_upper and first_lower < t_barrier:
                labels[i] = -1  # 閫貊１??
            else:
                labels[i] = 0   # 頞??箏
                
        self.df['Label_Triple_Barrier'] = labels
        
        # ?冽??敺?t_barrier 憭拍瘜?皜祆靘?鞈?
        self.df = self.df.iloc[:-t_barrier].copy()
        
        # ?箇泵????憿 (XGBoost Classifier)嚗????格?蝪∪??箝?行????押?        self.df['Label_Buy'] = np.where(self.df['Label_Triple_Barrier'] == 1, 1, 0)
        
        return self.df
