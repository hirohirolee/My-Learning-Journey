import streamlit as st
st.title('ensemble_voting.py - 自動化展示')
st.info('這是從原專案腳本自動包裝產生的互動式介面。')

import numpy as np
from typing import Dict, Any, List

class FourKingsVotingEngine:
    """
    四大金剛聯合投票引擎 (XGBoost, LightGBM, Random Forest, LSTM)
    實作嚴格的「硬投票 (Hard Voting)」機制
    """
    def __init__(self, models: Dict[str, Any]):
        """
        初始化需傳入四個訓練好的模型實例
        :param models: {'xgb': model1, 'lgb': model2, 'rf': model3, 'lstm': model4}
        """
        required_keys = {'xgb', 'lgb', 'rf', 'lstm'}
        if not required_keys.issubset(models.keys()):
            raise ValueError(f"必須包含四大模型：{required_keys}")
        
        self.models = models

    def predict_signal(self, feature_data_ml: np.ndarray, feature_data_dl: Any) -> int:
        """
        取得最終決策訊號
        :param feature_data_ml: 機器學習模型用的特徵資料 (2D array)
        :param feature_data_dl: 深度學習模型用的特徵序列 (Tensor)
        :return: 1 代表強烈買進，0 代表觀望
        """
        # 取得各模型預測結果 (假設模型 .predict() 回傳 1 為看漲，0 為看跌/盤整)
        # 實作上可依據模型封裝方式調整呼叫方法
        pred_xgb = self.models['xgb'].predict(feature_data_ml)[0]
        pred_lgb = self.models['lgb'].predict(feature_data_ml)[0]
        pred_rf = self.models['rf'].predict(feature_data_ml)[0]
        
        # LSTM 預測 (假設有提供封裝好的預測方法，或自己處理 Tensor 與 sigmoid 閥值)
        # 這裡假設大於 0.5 為 1
        import torch
        self.models['lstm'].eval()
        with torch.no_grad():
            lstm_prob = self.models['lstm'](feature_data_dl).item()
            pred_lstm = 1 if lstm_prob >= 0.5 else 0

        predictions = [pred_xgb, pred_lgb, pred_rf, pred_lstm]
        
        # 嚴格硬投票：必須四個模型全數為 1，才給出 1 的買進訊號
        if sum(predictions) == 4:
            return 1
        return 0
