import streamlit as st
st.title('strategy_breakout.py - 自動化展示')
st.info('這是從原專案腳本自動包裝產生的互動式介面。')

import backtrader as bt
from utils.logger import get_logger

logger = get_logger(__name__)

class BreakoutStrategy(bt.Strategy):
    """
    4.4 策略 2：Highest High 追高突破策略
    進場：價格突破過去 N 日新高
    出場：觸發固定百分比停損或停利
    """
    params = (
        ('highest_period', 20),
        ('stop_loss_pct', 0.05),
        ('take_profit_pct', 0.15),
    )

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        logger.debug(f'[{dt.isoformat()}] {txt}')

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.datahigh = self.datas[0].high
        self.order = None
        
        # 定義創 N 日新高指標
        self.highest = bt.indicators.Highest(self.datahigh(-1), period=self.params.highest_period)
        self.buy_price = 0.0

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
            
        if order.status in [order.Completed]:
            if order.isbuy():
                self.buy_price = order.executed.price
                self.log(f'進場買入成交, 價格: {self.buy_price:.2f}')
            elif order.issell():
                self.log(f'出場賣出成交, 價格: {order.executed.price:.2f}')
                
        self.order = None

    def notify_trade(self, trade):
        if trade.isclosed:
            self.log(f'交易平倉, 淨利: {trade.pnlcomm:.2f}')

    def next(self):
        if self.order:
            return

        # 尚未持有部位
        if not self.position:
            # 突破 N 日新高
            if self.dataclose[0] > self.highest[0]:
                self.log(f'突破 {self.params.highest_period} 日新高，進場！')
                self.order = self.buy()
                
        # 持有部位 (執行固定停損停利)
        else:
            current_price = self.dataclose[0]
            loss_threshold = self.buy_price * (1.0 - self.params.stop_loss_pct)
            profit_threshold = self.buy_price * (1.0 + self.params.take_profit_pct)
            
            if current_price <= loss_threshold:
                self.log(f'觸及停損 ({self.params.stop_loss_pct*100}%), 價格: {current_price:.2f}')
                self.order = self.sell()
            elif current_price >= profit_threshold:
                self.log(f'觸及停利 ({self.params.take_profit_pct*100}%), 價格: {current_price:.2f}')
                self.order = self.sell()
