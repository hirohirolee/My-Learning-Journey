import streamlit as st
st.title('model_evaluator.py - 自動化展示')
st.info('這是從原專案腳本自動包裝產生的互動式介面。')

﻿import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
import logging

logger = logging.getLogger(__name__)

class ModelEvaluator:
    """
    璅∪?蝮暹?閰摯璅∠?嚗?    ??鈭斗?銝??芰? Accuracy嚗?????Precision (?踹??????渲?? ??F1-Score??    """
    @staticmethod
    def evaluate(y_true, y_pred_prob, threshold=0.5):
        """
        蝬?閰摯??璅∪???蝔桃絞閮?璅?        
        :param threshold: 瘙箇??曉潘?憭扳甇文潭??澆鈭斗?閮?
        """
        # ?寞??曉潭捱摰?西眺??        y_pred = (y_pred_prob >= threshold).astype(int)
        
        acc = accuracy_score(y_true, y_pred)
        prec = precision_score(y_true, y_pred, zero_division=0)
        rec = recall_score(y_true, y_pred, zero_division=0)
        f1 = f1_score(y_true, y_pred, zero_division=0)
        
        try:
            auc = roc_auc_score(y_true, y_pred_prob)
        except ValueError:
            auc = 0.5 # ??璆萇垢??銝?y_true ?芣??桐?憿???            
        logger.info("========== AI 璅∪?蝮暹?閰摯?勗? ==========")
        logger.info(f"璅∪?瘙箇??瑼?(Threshold): {threshold}")
        logger.info(f"Accuracy (皞Ⅱ??  : {acc:.4f} (?葫甇?Ⅱ??靘?")
        logger.info(f"Precision(蝎曄Ⅱ??  : {prec:.4f} (?葫?撞嚗??撞??靘?- ?脩戌?扳?璅?")
        logger.info(f"Recall   (?砍???  : {rec:.4f} (???撞嚗芋???啁?瘥? - ?餅??扳?璅?")
        logger.info(f"F1-Score (隤踹?撟喳?): {f1:.4f} (撟唾﹛?脩戌???")
        logger.info(f"ROC AUC  (?脩??Ｙ?): {auc:.4f} (璅∪????賢??蜇?”??")
        logger.info("=========================================")
        
        return {
            'accuracy': acc,
            'precision': prec,
            'recall': rec,
            'f1_score': f1,
            'roc_auc': auc
        }
