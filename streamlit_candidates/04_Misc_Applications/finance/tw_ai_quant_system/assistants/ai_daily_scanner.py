import streamlit as st
st.title('ai_daily_scanner.py - 自動化展示')
st.info('這是從原專案腳本自動包裝產生的互動式介面。')

import pandas as pd
import logging
from data_pipeline.market_data import MarketDataLoader
from feature_engineering.technical_features import TechnicalFeatureEngineer
from ai_models.xgboost_predictor import XGBoostPredictor

logger = logging.getLogger(__name__)

class AIDailyScanner:
    """
    自動化 AI 小幫手：
    每日自動跑完 Data Pipeline -> Feature Engineering -> Model Inference。
    無須人工盯盤，自動產出「AI 高勝率預測清單」。
    """
    def __init__(self, model_path: str = None):
        # 實務上這裡會使用 joblib.load 載入已訓練好的 XGBoost 模型與 Scaler
        # 此處僅為架構示範
        self.predictor = XGBoostPredictor()
        self.trained = False # 標記模型是否已準備好

    def scan_market(self, stock_list: list, trained_features: list) -> pd.DataFrame:
        """
        對清單中的每一檔股票進行 Inference (推論預測)。
        
        :param stock_list: 監控的股票代碼清單
        :param trained_features: 訓練時使用的特徵欄位順序，確保矩陣形狀一致
        :return: 依據勝率排序的 DataFrame
        """
        # 實際應用中需移除此阻擋，或是先確保模型已載入
        # if not self.trained:
        #     logger.warning("模型尚未訓練/載入！請先訓練模型。")
        #     return pd.DataFrame()
            
        logger.info(f"啟動 AI 每日掃描，目標 {len(stock_list)} 檔個股...")
        results = []
        
        for stock in stock_list:
            try:
                # 1. 抓取最新資料 (含今日)
                loader = MarketDataLoader(stock)
                df = loader.fetch_history(period='3mo')
                if df.empty: continue
                
                # 2. 自動化特徵工程
                fe = TechnicalFeatureEngineer(df)
                df_features = fe.add_ta_features()
                
                # 確保所需特徵都存在
                missing_cols = [c for c in trained_features if c not in df_features.columns]
                if missing_cols:
                    logger.warning(f"{stock} 缺少模型所需特徵: {missing_cols}")
                    continue
                
                # 取出最新一天的資料列，準備進行推論
                latest_features = df_features.iloc[[-1]][trained_features].values
                
                # 3. AI 預測機率 (Inference)
                # 由於這裡示範用的模型尚未真正 fit()，所以呼叫 predict_proba 會報錯
                # 實戰中這裡會輸出真實的 0.0 ~ 1.0 勝率
                prob = 0.5 # 假設值
                
                results.append({
                    'StockCode': stock,
                    'Close': df_features['Close'].iloc[-1],
                    'AI_Win_Prob': prob
                })
                
            except Exception as e:
                logger.error(f"掃描 {stock} 時發生錯誤: {str(e)}")
                
        res_df = pd.DataFrame(results)
        if not res_df.empty:
            # 依據 AI 預測的勝率由高至低排序
            res_df = res_df.sort_values('AI_Win_Prob', ascending=False)
            logger.info("AI 掃描完成！高勝率清單已產出。")
            
        return res_df
