import pandas as pd
import numpy as np
from typing import List, Dict
from utils.logger import get_logger

logger = get_logger(__name__)

class FeatureEngineeringInterface:
    """
    Chapter 05: AI 與大數據架構介面 (特徵工程預處理)
    
    此模組作為未來串接機器學習 (Machine Learning) 與深度學習 (Deep Learning) 模型的橋樑。
    負責將歷史股價、技術指標 (TA) 以及新聞情緒分數 (NLP) 進行合併、正規化與標籤化。
    """
    def __init__(self):
        # 初始化，預留位置可載入預訓練的 NLP 情緒字典或 Transformer 模型 (例如 BERT)
        pass

    def merge_price_and_news(self, price_df: pd.DataFrame, news_data: List[Dict]) -> pd.DataFrame:
        """
        將新聞資料與股價歷史資料以「日期」為鍵進行合併 (Left Join)。
        未來的量化策略將可綜合「價格技術面」與「新聞消息面」進行多維度預測。
        """
        logger.info("準備合併股價與新聞情緒資料...")
        try:
            news_df = pd.DataFrame(news_data)
            if not news_df.empty and 'date' in news_df.columns:
                # 正規化日期格式
                news_df['date'] = pd.to_datetime(news_df['date']).dt.date
                
                # 假設外部 NLP 系統已經幫忙算好 Sentiment_Score，這裡產生模擬資料示範
                if 'Sentiment_Score' not in news_df.columns:
                    news_df['Sentiment_Score'] = np.random.uniform(-1.0, 1.0, size=len(news_df))
                
                # 將同一天的新聞情緒進行平均彙整
                daily_sentiment = news_df.groupby('date')['Sentiment_Score'].mean().reset_index()
                daily_sentiment.rename(columns={'date': 'Date'}, inplace=True)
                
                # 處理股價資料的日期索引
                if isinstance(price_df.index, pd.DatetimeIndex):
                    price_df = price_df.copy()
                    price_df['Date'] = price_df.index.date
                
                # 合併資料
                merged_df = pd.merge(price_df, daily_sentiment, on='Date', how='left')
                
                # 缺失值填補 (無新聞的日子，情緒分數設為中性 0.0)
                merged_df['Sentiment_Score'].fillna(0.0, inplace=True)
                merged_df.set_index('Date', inplace=True)
                
                logger.info("特徵資料合併成功")
                return merged_df
            else:
                logger.warning("新聞資料為空或缺少日期欄位，返回原始股價資料")
                return price_df
                
        except Exception as e:
            logger.error(f"特徵合併失敗: {str(e)}")
            return price_df

    def create_labels(self, df: pd.DataFrame, target_col: str = 'Close', horizon: int = 5) -> pd.DataFrame:
        """
        建立機器學習預測目標 (Labels / Y)。
        示範：預測未來 5 天後的收盤價是否高於今日 (分類問題)。
        """
        try:
            logger.info(f"建立機器學習預測標籤，預測跨度: {horizon} 天")
            
            # 將目標特徵向上平移 N 天 (代表未來的價格)
            df[f'Target_{horizon}d_Price'] = df[target_col].shift(-horizon)
            
            # 分類標籤：未來上漲為 1，下跌為 0
            df[f'Target_{horizon}d_Up'] = np.where(
                df[f'Target_{horizon}d_Price'] > df[target_col], 1, 0
            )
            
            # 注意：使用了 shift 會導致資料末端產生 NaN，在模型訓練 (fit) 前需 dropna
            return df
            
        except Exception as e:
            logger.error(f"建立預測標籤失敗: {str(e)}")
            raise

    def get_features_and_labels(self, df: pd.DataFrame, feature_cols: List[str], label_col: str):
        """
        將 DataFrame 轉換為 scikit-learn / XGBoost 等模型可直接吃進去的 NumPy 矩陣格式 (X, Y)
        """
        try:
            # 剔除包含 NaN 的資料列，確保矩陣乾淨
            clean_df = df.dropna(subset=feature_cols + [label_col])
            
            X = clean_df[feature_cols].values
            y = clean_df[label_col].values
            
            logger.info(f"萃取完成，特徵矩陣大小: {X.shape}, 標籤大小: {y.shape}")
            return X, y
        except Exception as e:
            logger.error(f"萃取特徵矩陣失敗: {str(e)}")
            raise
