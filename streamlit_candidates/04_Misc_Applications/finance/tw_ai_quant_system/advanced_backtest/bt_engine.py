import streamlit as st

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import backtrader as bt
import pandas as pd
from config import COMMISSION_RATE, TAX_RATE, SLIPPAGE
import logging

logger = logging.getLogger(__name__)

class TWStockCommission(bt.CommInfoBase):
    params = (
        ('commission', COMMISSION_RATE),
        ('tax', TAX_RATE),
        ('stocklike', True),
        ('commtype', bt.CommInfoBase.COMM_PERC),
    )

    def _getcommission(self, size, price, pseudoexec):
        if size > 0:  # Buy
            return abs(size) * price * self.p.commission
        elif size < 0:  # Sell
            return abs(size) * price * (self.p.commission + self.p.tax)
        return 0

class AdvancedBacktestEngine:
    def __init__(self, initial_cash: float = 1000000.0):
        self.cerebro = bt.Cerebro()
        self.cerebro.broker.setcash(initial_cash)
        
        # Setup commission
        comminfo = TWStockCommission()
        self.cerebro.broker.addcommissioninfo(comminfo)
        self.cerebro.broker.set_slippage_perc(perc=SLIPPAGE)
        
        # Add analyzers
        try:
            self.cerebro.addanalyzer(bt.analyzers.PyFolio, _name='pyfolio')
            self.cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
            self.cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
        except Exception as e:
            logger.warning(f"Error: {str(e)}")
        
    def add_data(self, datafeed):
        self.cerebro.adddata(datafeed)
        
    def add_strategy(self, strategy_cls, **kwargs):
        self.cerebro.addstrategy(strategy_cls, **kwargs)
        
    def run(self):
        logger.info(f"Running backtest (Cash: {self.cerebro.broker.getvalue():.2f})")
        results = self.cerebro.run()
        logger.info(f"Backtest finished (Final value: {self.cerebro.broker.getvalue():.2f})")
        return results

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    st.write("Testing AdvancedBacktestEngine...")
    engine = AdvancedBacktestEngine(initial_cash=1000000)
    st.write("Engine initialized with 1,000,000 cash.")
