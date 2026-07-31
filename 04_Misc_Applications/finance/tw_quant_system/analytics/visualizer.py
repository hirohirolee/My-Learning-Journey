import pandas as pd
import matplotlib.pyplot as plt
import mplfinance as mpf
from utils.logger import get_logger

logger = get_logger(__name__)

class ChartVisualizer:
    """
    3.3 視覺化模組：
    繪製包含 K 棒、布林通道與成交量子圖的專業圖表。
    使用 mplfinance 套件來呈現生產環境等級的 K 線圖。
    """
    @staticmethod
    def plot_kline_with_bb(df: pd.DataFrame, title: str = "Stock Chart", save_path: str = None):
        """
        繪製專業 K 線圖與布林通道。
        
        :param df: 包含 OHLCV 與 BB_Upper, BB_Mid, BB_Lower 的 DataFrame
        :param title: 圖表標題
        :param save_path: 儲存路徑，若無則顯示於畫面
        """
        try:
            logger.info(f"開始繪製圖表: {title}")
            
            # 確保索引為 DatetimeIndex (mplfinance 的要求)
            if not isinstance(df.index, pd.DatetimeIndex):
                df.index = pd.to_datetime(df.index)
            
            # 準備附加圖表 (布林通道)
            apds = []
            if all(col in df.columns for col in ['BB_Upper', 'BB_Mid', 'BB_Lower']):
                apds = [
                    mpf.make_addplot(df['BB_Upper'], color='r', linestyle='--'),
                    mpf.make_addplot(df['BB_Mid'], color='b', linestyle='-'),
                    mpf.make_addplot(df['BB_Lower'], color='g', linestyle='--')
                ]
            
            # 設定樣式 (Yahoo Finance 風格，紅漲綠跌)
            mc = mpf.make_marketcolors(up='r', down='g', edge='i', wick='i', volume='in')
            s = mpf.make_mpf_style(marketcolors=mc, gridstyle=':', y_on_right=True)
            
            # 繪圖設定
            kwargs = dict(
                type='candle',
                volume=True,
                title=title,
                style=s,
                addplot=apds,
                figsize=(12, 8)
            )
            
            if save_path:
                mpf.plot(df, **kwargs, savefig=save_path)
                logger.info(f"圖表已儲存至 {save_path}")
            else:
                mpf.plot(df, **kwargs)
                
        except Exception as e:
            logger.error(f"繪圖失敗: {str(e)}")
            raise
