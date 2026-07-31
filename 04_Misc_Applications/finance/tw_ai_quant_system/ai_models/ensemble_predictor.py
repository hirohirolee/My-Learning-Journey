import pandas as pd
import numpy as np
from typing import Tuple, List, Dict
import logging
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnsembleVotingPredictor:
    """
    三模型投票機制 (Ensemble Voting) 預測器。
    結合 XGBoost, LightGBM 與 Random Forest 三大強勢模型。
    必須三個模型同時看漲 (預測為 1)，最終訊號才會是 1。
    """
    
    def __init__(self, random_state: int = 42):
        """
        初始化三位 AI 老頭家 (大寶、二寶、三寶)。
        """
        self.random_state = random_state
        
        # 建立三個不同的機器學習分類器
        # 大寶：XGBoost (善於處理極端值與複雜非線性關係)
        self.model_xgb = XGBClassifier(
            n_estimators=100, 
            learning_rate=0.05, 
            random_state=self.random_state,
            use_label_encoder=False,
            eval_metric='logloss'
        )
        
        # 二寶：LightGBM (訓練速度快，對大型數據集特別敏感)
        self.model_lgb = LGBMClassifier(
            n_estimators=100,
            learning_rate=0.05,
            random_state=self.random_state,
            verbose=-1
        )
        
        # 三寶：Random Forest (隨機森林，最穩健不易過擬合，負責把關)
        self.model_rf = RandomForestClassifier(
            n_estimators=100,
            max_depth=5,
            random_state=self.random_state
        )
        
        self.is_trained = False

    def train_models(self, X_train: pd.DataFrame, y_train: pd.Series) -> Dict[str, float]:
        """
        訓練三個 AI 模型。
        
        Args:
            X_train (pd.DataFrame): 訓練特徵矩陣
            y_train (pd.Series): 訓練目標標籤 (1: 漲, 0: 跌)
            
        Returns:
            Dict[str, float]: 回傳三個模型在訓練集上的準確率 (供參考)
        """
        logger.info("開始讓三位 AI 老頭家進行魔鬼訓練...")
        
        try:
            # 訓練 XGBoost
            logger.info("訓練大寶 (XGBoost) 中...")
            self.model_xgb.fit(X_train, y_train)
            acc_xgb = accuracy_score(y_train, self.model_xgb.predict(X_train))
            
            # 訓練 LightGBM
            logger.info("訓練二寶 (LightGBM) 中...")
            self.model_lgb.fit(X_train, y_train)
            acc_lgb = accuracy_score(y_train, self.model_lgb.predict(X_train))
            
            # 訓練 Random Forest
            logger.info("訓練三寶 (Random Forest) 中...")
            self.model_rf.fit(X_train, y_train)
            acc_rf = accuracy_score(y_train, self.model_rf.predict(X_train))
            
            self.is_trained = True
            logger.info("三位老頭家訓練完畢！")
            
            return {
                "XGBoost_Acc": round(acc_xgb, 4),
                "LightGBM_Acc": round(acc_lgb, 4),
                "RandomForest_Acc": round(acc_rf, 4)
            }
            
        except Exception as e:
            logger.error(f"模型訓練失敗: {str(e)}")
            raise

    def predict_signals(self, X_test: pd.DataFrame) -> Tuple[np.ndarray, pd.DataFrame]:
        """
        使用三模型進行嚴格投票預測 (Hard Voting)。
        三個模型都預測 1，結果才為 1，否則為 0。
        
        Args:
            X_test (pd.DataFrame): 測試特徵矩陣
            
        Returns:
            Tuple[np.ndarray, pd.DataFrame]:
                - 最終投票訊號陣列 (1 或 0)
                - 包含三個模型各自投票紀錄的 DataFrame (方便前端 UI 呈現)
        """
        if not self.is_trained:
            raise ValueError("模型尚未訓練！請先呼叫 train_models()。")
            
        logger.info("開始進行三方會審 (預測投票)...")
        
        # 分別取得三個模型的預測結果
        pred_xgb = self.model_xgb.predict(X_test)
        pred_lgb = self.model_lgb.predict(X_test)
        pred_rf = self.model_rf.predict(X_test)
        
        # 將投票結果整理成 DataFrame 供介面展示
        voting_details = pd.DataFrame({
            "大寶_投票": pred_xgb,
            "二寶_投票": pred_lgb,
            "三寶_投票": pred_rf
        }, index=X_test.index)
        
        # 嚴格投票邏輯：三個陣列相加，必須等於 3 才代表全票通過
        total_votes = pred_xgb + pred_lgb + pred_rf
        final_signal = np.where(total_votes == 3, 1, 0)
        
        voting_details['全票通過'] = final_signal
        
        logger.info(f"預測完成。在 {len(X_test)} 筆資料中，有 {final_signal.sum()} 筆獲得全票通過。")
        
        return final_signal, voting_details

if __name__ == "__main__":
    # 簡單的本地測試
    # 生成隨機假資料
    X_dummy = pd.DataFrame(np.random.randn(100, 5), columns=['f1', 'f2', 'f3', 'f4', 'f5'])
    y_dummy = pd.Series(np.random.randint(0, 2, 100))
    
    predictor = EnsembleVotingPredictor()
    acc = predictor.train_models(X_dummy, y_dummy)
    print("訓練準確率:", acc)
    
    X_new = pd.DataFrame(np.random.randn(10, 5), columns=['f1', 'f2', 'f3', 'f4', 'f5'])
    signals, details = predictor.predict_signals(X_new)
    print("\n投票明細:\n", details)
