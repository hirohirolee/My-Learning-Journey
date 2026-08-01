import streamlit as st

import backtrader as bt
import pandas as pd
from utils.logger import get_logger

logger = get_logger(__name__)

class BacktestEngine:
    """
    4.1 & 4.2 Backtrader 基礎回測框架與 Pyfolio 串接
    封裝 Cerebro 的初始化、資料載入、策略加入與績效分析。
    可優雅處理 FileNotFoundError 或 ImportError。
    """
    def __init__(self, initial_cash: float = 1000000.0, commission: float = 0.001425):
        self.cerebro = bt.Cerebro()
        # 設定初始資金
        self.cerebro.broker.setcash(initial_cash)
        # 設定台股常見手續費率
        self.cerebro.broker.setcommission(commission=commission)
        
        try:
            # 加入 Pyfolio 分析器以便後續計算每日資產報酬率與績效
            self.cerebro.addanalyzer(bt.analyzers.PyFolio, _name='pyfolio')
            # 加入其他常見分析器
            self.cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
            self.cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
        except Exception as e:
            logger.error(f"加入 Analyzer 失敗: {str(e)}")

    def add_data(self, df: pd.DataFrame, data_name: str = "Stock"):
        """載入 Pandas DataFrame 歷史資料至 Cerebro"""
        try:
            if df.empty:
                raise ValueError("DataFrame 為空，無法載入資料")
                
            if not isinstance(df.index, pd.DatetimeIndex):
                df.index = pd.to_datetime(df.index)
            
            data = bt.feeds.PandasData(
                dataname=df,
                name=data_name
            )
            self.cerebro.adddata(data)
            logger.info(f"成功載入資料: {data_name} ({len(df)} 筆)")
        except AttributeError as e:
            logger.error(f"資料欄位有誤，請確認 DataFrame 包含 OHLCV: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"載入資料失敗: {str(e)}")
            raise

    def add_strategy(self, strategy_cls, **kwargs):
        """加入一般回測策略"""
        self.cerebro.addstrategy(strategy_cls, **kwargs)

    def optimize_strategy(self, strategy_cls, **kwargs):
        """加入參數最佳化 (Grid Search) 策略"""
        self.cerebro.optstrategy(strategy_cls, **kwargs)

    def run(self) -> list:
        """執行回測並回傳結果清單"""
        logger.info(f"開始執行回測，初始資金: {self.cerebro.broker.getvalue():.2f}")
        try:
            results = self.cerebro.run()
            final_value = self.cerebro.broker.getvalue()
            logger.info(f"回測結束，最終資金: {final_value:.2f}")
            return results
        except Exception as e:
            logger.error(f"回測執行過程發生錯誤: {str(e)}", exc_info=True)
            return []

    def get_pyfolio_returns(self, results: list):
        """
        從回測結果中解析 Pyfolio 所需的每日資產報酬率 (Returns)。
        此處需小心處理 pyfolio 套件可能未安裝的 ImportError。
        """
        try:
            strat = results[0]
            if isinstance(results[0], list): # 若為 Grid Search，results 會是二維陣列
                strat = results[0][0]
                
            pyfoliozer = strat.analyzers.getbyname('pyfolio')
            returns, positions, transactions, gross_lev = pyfoliozer.get_pf_items()
            return returns
        except ImportError:
            logger.error("無法載入 Pyfolio 分析模組，請確保已安裝 pyfolio 套件")
            return None
        except Exception as e:
            logger.error(f"解析 Pyfolio 報酬率失敗: {str(e)}")
            return None
