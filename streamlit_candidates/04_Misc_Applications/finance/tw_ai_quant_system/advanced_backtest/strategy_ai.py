import streamlit as st
st.title('strategy_ai.py - 自動化展示')
st.info('這是從原專案腳本自動包裝產生的互動式介面。')

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import backtrader as bt
import logging

logger = logging.getLogger(__name__)

class PandasDataWithAI(bt.feeds.PandasData):
    """
    ?芾? DataFeed嚗?閮梯??亙葆??AI ?葫璈?甈? (ai_prob) ??DataFrame??    """
    lines = ('ai_prob',)
    # 撠?DataFrame 銝剔? 'AI_Prob' 甈????圈?蝺?(?亦??閮?-1 ?芸?撠?)
    params = (('ai_prob', -1),) 

class AIStrategy(bt.Strategy):
    """
    ?箸 XGBoost ?葫閮??漱???乓?    ?脣?渡 AI 璅∪?璈?瘙箏?嚗雿之撠????KellySizer 瘙箏???    """
    params = (
        ('buy_threshold', 0.60),  # AI ???葫憭扳 60% ?脣
        ('sell_threshold', 0.40), # AI ???葫頝 40% (頧摹) ?箏
        ('stop_loss_pct', 0.05),  # 靽??祕擃?澆?????(5%)
    )

    def __init__(self):
        self.ai_prob = self.datas[0].ai_prob
        self.close = self.datas[0].close
        self.order = None
        self.buy_price = 0.0
        
        # ?湧甇方??訾? KellySizer 霈??蝞?雿喳?
        self.current_ai_prob = 0.0

    def next(self):
        if self.order: return
            
        self.current_ai_prob = self.ai_prob[0]
        current_date = self.datas[0].datetime.date(0)

        if not self.position:
            # 擃??脣 (??Sizer 瘙箏?鞎瑕?撠?
            if self.current_ai_prob >= self.params.buy_threshold:
                logger.info(f"[{current_date}] AI 撘瑞??? (璈?: {self.current_ai_prob:.2f}) -> 鞎琿脰???")
                self.order = self.buy()
        else:
            # 閮?頧摹?孛??蝺???箏
            if self.current_ai_prob <= self.params.sell_threshold:
                logger.info(f"[{current_date}] AI ?征/閮?頧摹 (璈?: {self.current_ai_prob:.2f}) -> 撟喳??")
                self.order = self.sell()
            elif self.close[0] < self.buy_price * (1 - self.params.stop_loss_pct):
                logger.info(f"[{current_date}] 閫貊撖阡?摨??? -> ???箏")
                self.order = self.sell()

    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                self.buy_price = order.executed.price
        self.order = None
