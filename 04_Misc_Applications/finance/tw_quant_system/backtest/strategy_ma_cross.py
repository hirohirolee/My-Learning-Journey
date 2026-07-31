import backtrader as bt
from utils.logger import get_logger

logger = get_logger(__name__)

class MACrossStrategy(bt.Strategy):
    """
    4.3 策略 1：5MA / 60MA 穿越策略
    進場：5MA 上穿 60MA
    出場：跌破 60MA
    
    (支援 Grid Search 演算最適參數)
    """
    params = (
        ('fast_ma', 5),
        ('slow_ma', 60),
    )

    def log(self, txt, dt=None):
        """Backtrader 標準日誌記錄函式"""
        dt = dt or self.datas[0].datetime.date(0)
        logger.debug(f'[{dt.isoformat()}] {txt}')

    def __init__(self):
        """初始化生命週期：定義資料與技術指標"""
        self.dataclose = self.datas[0].close
        self.order = None
        
        # 宣告技術指標
        self.fast_sma = bt.indicators.SimpleMovingAverage(
            self.datas[0], period=self.params.fast_ma)
        self.slow_sma = bt.indicators.SimpleMovingAverage(
            self.datas[0], period=self.params.slow_ma)
            
        # 交叉訊號: 1 代表 fast 往上穿越 slow, -1 代表往下穿越
        self.crossover = bt.indicators.CrossOver(self.fast_sma, self.slow_sma)

    def notify_order(self, order):
        """訂單狀態改變時觸發"""
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'買入成交, 價格: {order.executed.price:.2f}, 成本: {order.executed.value:.2f}, 手續費: {order.executed.comm:.2f}')
            elif order.issell():
                self.log(f'賣出成交, 價格: {order.executed.price:.2f}, 成本: {order.executed.value:.2f}, 手續費: {order.executed.comm:.2f}')
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log(f'訂單未成交 (狀態碼: {order.status})')

        self.order = None

    def notify_trade(self, trade):
        """一筆完整交易 (買與賣閉環) 完成時觸發"""
        if not trade.isclosed:
            return
        self.log(f'交易獲利結算, 淨利: {trade.pnlcomm:.2f}')

    def next(self):
        """每個時間點 (每根 K 棒) 的核心運算邏輯"""
        if self.order:
            return # 有待處理訂單時不動作，避免重複下單

        # 若目前無持倉
        if not self.position:
            if self.crossover > 0:
                self.log(f'發出買入訊號, 價格: {self.dataclose[0]:.2f}')
                self.order = self.buy()
        # 若已有持倉
        else:
            # 跌破慢線 (60MA) 即出場停損/停利
            if self.dataclose[0] < self.slow_sma[0]:
                self.log(f'跌破慢線，發出賣出訊號, 價格: {self.dataclose[0]:.2f}')
                self.order = self.sell()
