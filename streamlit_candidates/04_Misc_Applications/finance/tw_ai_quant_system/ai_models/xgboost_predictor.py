import streamlit as st

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import GridSearchCV
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
import logging
from typing import Tuple, List

logger = logging.getLogger(__name__)

class XGBoostPredictor:
    """
    AI 璅∪?璅∠?嚗?    撠? XGBoost 瞍?瘜????芸????孵噩蝮格?ridSearch 頞??豢?雿喳?嚗?    銝血閬死???漱??????Feature Importance??    """
    def __init__(self):
        # 雿輻 XGBClassifier ?葫??璈? (鈭???)
        self.model = xgb.XGBClassifier(
            eval_metric='logloss',
            random_state=42
        )
        self.scaler = StandardScaler()
        self.feature_names = []
        
    def prepare_data(self, df: pd.DataFrame, features: List[str], target: str) -> Tuple:
        """
        ???摨??鞈???銝阡脰??孵噩璅???        ???葫銝哨??渡??冽??? (Shuffle) 鞈?嚗???交靘???(Look-ahead Bias)??        """
        logger.info("皞?璅∪?閮毀鞈?嚗蝭?Look-ahead Bias...")
        self.feature_names = features
        
        df_clean = df.dropna(subset=features + [target])
        
        X = df_clean[features].values
        y = df_clean[target].values
        
        # ???摨?? (??80% 閮毀嚗? 20% 皜祈岫)
        split_idx = int(len(X) * 0.8)
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        
        # ? Train ?脰? fitted scale嚗甇?Test 鞈?瘣拇??啁葬?曉銝?        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        return X_train_scaled, X_test_scaled, y_train, y_test

    def train_with_gridsearch(self, X_train, y_train):
        """Train with GridSearch"""
        logger.info("?? XGBoost 頞??貊雯?潭?蝝?..")
        
        param_grid = {
            'max_depth': [3, 5],
            'learning_rate': [0.01, 0.05],
            'n_estimators': [100, 200]
        }
        
        grid_search = GridSearchCV(
            estimator=self.model,
            param_grid=param_grid,
            scoring='roc_auc', # ???葫撣貊???AUC ?
            cv=3,
            verbose=1
        )
        
        grid_search.fit(X_train, y_train)
        self.model = grid_search.best_estimator_
        logger.info(f"蝬脫?揣摰嚗?雿唾??蝯?: {grid_search.best_params_}")
        
    def predict_proba(self, X) -> np.ndarray:
        """Predict probabilities"""
        X_scaled = self.scaler.transform(X)
        return self.model.predict_proba(X_scaled)[:, 1]

    def plot_feature_importance(self, save_path: str = None):
        """Plot feature importances"""
        logger.info("Plotting feature importances")
        importances = self.model.feature_importances_
        indices = np.argsort(importances)[::-1]
        
        plt.figure(figsize=(10, 6))
        plt.title("XGBoost Feature Importances in Quant Trading")
        plt.bar(range(len(self.feature_names)), importances[indices], align="center")
        plt.xticks(range(len(self.feature_names)), [self.feature_names[i] for i in indices], rotation=90)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path)
            logger.info(f"Saved feature importance plot to {save_path}")
        else:
            st.pyplot(plt.gcf())
