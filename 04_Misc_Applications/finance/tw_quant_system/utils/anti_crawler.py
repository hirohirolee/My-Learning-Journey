import random
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from config import USER_AGENTS, REQUEST_TIMEOUT, MAX_RETRIES
from utils.logger import get_logger

logger = get_logger(__name__)

class AntiCrawlerSession:
    """
    防爬蟲 HTTP Session 封裝類別，提供：
    1. User-Agent 隨機替換
    2. 隨機延遲 (模擬人類行為)
    3. HTTP 錯誤自動重試機制
    """
    def __init__(self) -> None:
        self.session = requests.Session()
        self._setup_retry_strategy()

    def _setup_retry_strategy(self) -> None:
        """
        設定 HTTP 請求失敗時的重試策略 (Retry Strategy)。
        """
        retry_strategy = Retry(
            total=MAX_RETRIES,
            backoff_factor=1.0,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def get_random_headers(self) -> dict:
        """
        獲取隨機的 HTTP Headers，替換 User-Agent 以對抗防爬蟲。
        
        :return: 包含隨機 User-Agent 的字典
        """
        return {
            'User-Agent': random.choice(USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
        }

    def random_sleep(self, min_sec: float = 1.0, max_sec: float = 3.0) -> None:
        """
        執行隨機延遲以模擬人類行為。
        
        :param min_sec: 最小延遲秒數
        :param max_sec: 最大延遲秒數
        """
        sleep_time = random.uniform(min_sec, max_sec)
        logger.debug(f"隨機延遲 {sleep_time:.2f} 秒...")
        time.sleep(sleep_time)

    def get(self, url: str, params: dict = None, **kwargs) -> requests.Response:
        """
        發送 GET 請求，具備防爬與異常處理機制。
        
        :param url: 目標網址
        :param params: Query Parameters
        :return: requests.Response 實例
        """
        headers = self.get_random_headers()
        if 'headers' in kwargs:
            headers.update(kwargs['headers'])
            del kwargs['headers']

        self.random_sleep()
        
        try:
            response = self.session.get(
                url, 
                params=params, 
                headers=headers, 
                timeout=REQUEST_TIMEOUT, 
                **kwargs
            )
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"請求失敗 URL: {url}, Error: {str(e)}")
            raise
        finally:
            logger.debug(f"完成請求 URL: {url}")
