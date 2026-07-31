import backtrader as bt
from utils.logger import get_logger

logger = get_logger(__name__)

class MacdMaStrategy(bt.Strategy):
    """
    4.5 策略 3：MACD 翻紅 + 多均線齊揚 (多股回測)
    進場條件：MACD 柱狀體由負轉正，且 短 > 中 > 長 MA。
    這支策略展示了如何迭代 `self.datas` 以支援多檔股票同時回測。
    """
    params = (
        ('ma_short', 5),
        ('ma_mid', 20),
        ('ma_long', 60),
    )

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        logger.debug(f'[{dt.isoformat()}] {txt}')

    def __init__(self):
        # 由於支援多商品，為每個資料集 (股票) 建立指標字典
        self.inds = dict()
        
        for d in self.datas:
            self.inds[d] = dict()
            # 宣告短中長期 MA
            self.inds[d]['ma_s'] = bt.indicators.SMA(d.close, period=self.params.ma_short)
            self.inds[d]['ma_m'] = bt.indicators.SMA(d.close, period=self.params.ma_mid)
            self.inds[d]['ma_l'] = bt.indicators.SMA(d.close, period=self.params.ma_long)
            
            # 宣告 MACD 指標
            self.inds[d]['macd'] = bt.indicators.MACDHisto(d.close)

    def next(self):
        # 遍歷回測中載入的所有股票
        for d in self.datas:
            pos = self.getposition(d).size
            
            # 判斷 MA 齊上揚 (短線 > 中線 > 長線)
            ma_uptrend = (self.inds[d]['ma_s'][0] > self.inds[d]['ma_m'][0]) and \
                         (self.inds[d]['ma_m'][0] > self.inds[d]['ma_l'][0])
                         
            # 判斷 MACD 柱狀體翻紅 (前一期為負，當期為正)
            macd_turn_red = (self.inds[d]['macd'].histo[-1] < 0) and \
                            (self.inds[d]['macd'].histo[0] > 0)
                            
            # 進場邏輯
            if pos == 0:
                if ma_uptrend and macd_turn_red:
                    self.log(f'[{d._name}] 觸發 MACD 翻紅且 MA 上揚，買入進場')
                    self.buy(data=d)
                    
            # 出場邏輯 (跌破中線 20MA，視為趨勢反轉)
            else:
                if d.close[0] < self.inds[d]['ma_m'][0]:
                    self.log(f'[{d._name}] 跌破月線，賣出平倉')
                    self.sell(data=d)
