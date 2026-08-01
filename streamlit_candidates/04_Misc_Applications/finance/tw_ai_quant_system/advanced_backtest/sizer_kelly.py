import streamlit as st

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import backtrader as bt
import logging

logger = logging.getLogger(__name__)

class KellySizer(bt.Sizer):
    """
    ??鞈??抒恣 (Money Management)嚗??AI ?葫璈???拙撘?(Kelly Criterion)
    ?砍?: f* = p - (q / b)
    p = ?脣璈? (??XGBoost ??)
    q = ?扳?璈? (1 - p)
    b = 鞈? (甇瑕?葫蝯梯??箇??瘥?
    """
    params = (
        ('win_loss_ratio', 1.5),      # ?身?瘥?1.5
        ('max_position_pct', 0.5),    # ?桃?鈭斗??€擃?頞?蝮質???50%嚗甇Ｙ??
        ('min_prob_threshold', 0.55), # ?葫璈?憭扳甇文€潭???勗銝
    )

    def _getsizing(self, comminfo, cash, data, isbuy):
        if not isbuy:
            # Sell
            return self.broker.getposition(data).size

        try:
            # 敺??乩葉?? AI ?葫???啣???(??strategy_ai.py 瘜典)
            ai_prob = self.strategy.current_ai_prob
        except AttributeError:
            logger.warning("蝑銝剜?潛 current_ai_prob嚗€€??摰雿?蝵?(10%)")
            return (cash * 0.1) // data.close[0]

        # ??AI 隤??銝?嚗?銝
        if ai_prob < self.p.min_prob_threshold:
            return 0 

        # ?勗?砍?閮?
        p = ai_prob
        q = 1.0 - p
        b = self.p.win_loss_ratio
        kelly_pct = p - (q / b)
        
        if kelly_pct <= 0:
            return 0
            
        # ?璆萇垢????(?勗?砍??撩暺瘜Ｗ?璆萄之嚗祕?啣虜雿輻 Half-Kelly)
        target_pct = min(kelly_pct, self.p.max_position_pct)
        
        # ???航眺?⊥
        target_cash = cash * target_pct
        size = target_cash // data.close[0]
        
        logger.info(f"AI?葫??: {ai_prob*100:.1f}% -> ?勗撱箄降?蔭: {kelly_pct*100:.1f}%, 撖阡?銝?⊥: {size}")
        return size
