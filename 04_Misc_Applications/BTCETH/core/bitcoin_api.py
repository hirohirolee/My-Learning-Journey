import time
from typing import Any, Dict, Optional
import requests
from loguru import logger
from config import settings

class BitcoinAPIManager:
    """管理獲取即時比特幣區塊鏈指標與市場價格數據的管理器。
    
    依序嘗試多個公共 API（mempool.space -> Blockchain.com -> CoinGecko），
    並在記憶體中快取結果，以避免頻繁請求觸發 API 頻率限制。
    """
    
    def __init__(self) -> None:
        self._cache: Dict[str, Any] = {}
        self._cache_timestamp: float = 0.0
        self.ttl: int = settings.API_CACHE_TTL_SEC
        self.max_retries: int = settings.API_MAX_RETRIES
        self.timeout: int = settings.API_TIMEOUT_SEC

    def _get_request_with_retries(self, url: str) -> Optional[requests.Response]:
        """執行帶有重試機制的 GET 請求。
        
        Args:
            url (str): 目標 URL。
            
        Returns:
            Optional[requests.Response]: 成功時返回 Response 對象，否則返回 None。
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.debug(f"發送 HTTP GET 請求至 {url} (嘗試 {attempt}/{self.max_retries})")
                response = requests.get(url, timeout=self.timeout)
                if response.status_code == 200:
                    return response
                logger.warning(f"請求失敗，狀態碼為 {response.status_code}，網址: {url}")
            except requests.RequestException as e:
                logger.warning(f"請求在第 {attempt} 次嘗試時發生異常，網址 {url}: {e}")
            if attempt < self.max_retries:
                time.sleep(1.0)
        return None

    def fetch_mempool_space(self) -> Optional[Dict[str, Any]]:
        """嘗試使用 mempool.space 的端點獲取所需數據。
        
        Returns:
            Optional[Dict[str, Any]]: 成功時返回解析後的數據字典，否則為 None。
        """
        try:
            logger.info("嘗試從 mempool.space 獲取數據")
            
            # 獲取幣價
            price_url = f"{settings.MEMPOOL_SPACE_URL}/v1/prices"
            price_res = self._get_request_with_retries(price_url)
            if not price_res:
                return None
            price_data = price_res.json()
            btc_price_usd = float(price_data.get("USD", settings.FALLBACK_BTC_PRICE_USD))

            # 獲取區塊高度
            height_url = f"{settings.MEMPOOL_SPACE_URL}/blocks/tip/height"
            height_res = self._get_request_with_retries(height_url)
            if not height_res:
                return None
            block_height = int(height_res.text.strip())

            # 獲取最近區塊（用以解析難度和手續費資訊）
            blocks_url = f"{settings.MEMPOOL_SPACE_URL}/blocks"
            blocks_res = self._get_request_with_retries(blocks_url)
            if not blocks_res:
                return None
            blocks = blocks_res.json()
            if not blocks:
                return None
            
            latest_block = blocks[0]
            difficulty = float(latest_block.get("difficulty", settings.FALLBACK_DIFFICULTY))
            
            # 從難度估算全網算力: 算力 = 難度 * 2^32 / 600
            hashrate_h_s = (difficulty * (2**32)) / 600.0

            # 從區塊 extras 獲取區塊獎勵與預估交易手續費（單位皆為 BTC）
            extras = latest_block.get("extras", {})
            # 區塊補貼獎勵 (聰 sats)
            reward_sats = extras.get("reward", 0)
            if reward_sats > 0:
                block_reward_btc = reward_sats / 1e8
            else:
                # 回退至基於區塊高度計算的補貼
                block_reward_btc = self._calculate_block_reward(block_height)
                
            total_fees_sats = extras.get("totalFees", 0)
            if total_fees_sats > 0:
                est_tx_fees_btc = total_fees_sats / 1e8
            else:
                est_tx_fees_btc = settings.FALLBACK_TX_FEES_BTC

            return {
                "btc_price_usd": btc_price_usd,
                "difficulty": difficulty,
                "hashrate_h_s": hashrate_h_s,
                "block_height": block_height,
                "block_reward_btc": block_reward_btc,
                "est_tx_fees_btc": est_tx_fees_btc,
                "source": "mempool.space"
            }
        except Exception as e:
            logger.error(f"從 mempool.space 獲取數據時發生錯誤: {e}")
            return None

    def fetch_blockchain_info(self) -> Optional[Dict[str, Any]]:
        """嘗試使用 Blockchain.com 的查詢端點獲取所需數據。
        
        Returns:
            Optional[Dict[str, Any]]: 成功時返回解析後的數據字典，否則為 None。
        """
        try:
            logger.info("嘗試從 Blockchain.com 獲取數據")
            
            # 獲取幣價
            price_url = f"{settings.BLOCKCHAIN_INFO_URL}/ticker"
            price_res = self._get_request_with_retries(price_url)
            if not price_res:
                return None
            btc_price_usd = float(price_res.json().get("USD", {}).get("last", settings.FALLBACK_BTC_PRICE_USD))

            # 獲取區塊高度
            height_url = f"{settings.BLOCKCHAIN_INFO_URL}/q/getblockcount"
            height_res = self._get_request_with_retries(height_url)
            if not height_res:
                return None
            block_height = int(height_res.text.strip())

            # 獲取難度
            diff_url = f"{settings.BLOCKCHAIN_INFO_URL}/q/getdifficulty"
            diff_res = self._get_request_with_retries(diff_url)
            if not diff_res:
                return None
            difficulty = float(diff_res.text.strip())

            # 獲取全網算力（Blockchain API 返回的單位是 GH/s）
            hr_url = f"{settings.BLOCKCHAIN_INFO_URL}/q/hashrate"
            hr_res = self._get_request_with_retries(hr_url)
            if hr_res:
                hashrate_h_s = float(hr_res.text.strip()) * 1e9  # 將 GH/s 轉為 H/s
            else:
                hashrate_h_s = (difficulty * (2**32)) / 600.0

            block_reward_btc = self._calculate_block_reward(block_height)
            est_tx_fees_btc = settings.FALLBACK_TX_FEES_BTC

            return {
                "btc_price_usd": btc_price_usd,
                "difficulty": difficulty,
                "hashrate_h_s": hashrate_h_s,
                "block_height": block_height,
                "block_reward_btc": block_reward_btc,
                "est_tx_fees_btc": est_tx_fees_btc,
                "source": "Blockchain.com"
            }
        except Exception as e:
            logger.error(f"從 Blockchain.com 獲取數據時發生錯誤: {e}")
            return None

    def fetch_coingecko(self) -> Optional[Dict[str, Any]]:
        """嘗試使用 CoinGecko 獲取比特幣價格。
        
        注意：CoinGecko 僅提供市場價格，其他區塊鏈指標將維持回退預設值。
        
        Returns:
            Optional[Dict[str, Any]]: 成功時返回部分填充的數據字典，否則為 None。
        """
        try:
            logger.info("嘗試從 CoinGecko 獲取價格")
            url = f"{settings.COINGECKO_URL}/simple/price?ids=bitcoin&vs_currencies=usd"
            res = self._get_request_with_retries(url)
            if not res:
                return None
            
            price_data = res.json()
            btc_price_usd = float(price_data.get("bitcoin", {}).get("usd", settings.FALLBACK_BTC_PRICE_USD))
            
            block_height = settings.FALLBACK_BLOCK_HEIGHT
            difficulty = settings.FALLBACK_DIFFICULTY
            hashrate_h_s = settings.FALLBACK_HASHRATE_EH * 1e18
            block_reward_btc = self._calculate_block_reward(block_height)
            est_tx_fees_btc = settings.FALLBACK_TX_FEES_BTC

            return {
                "btc_price_usd": btc_price_usd,
                "difficulty": difficulty,
                "hashrate_h_s": hashrate_h_s,
                "block_height": block_height,
                "block_reward_btc": block_reward_btc,
                "est_tx_fees_btc": est_tx_fees_btc,
                "source": "CoinGecko"
            }
        except Exception as e:
            logger.error(f"從 CoinGecko 獲取價格時發生錯誤: {e}")
            return None

    def _calculate_block_reward(self, height: int) -> float:
        """計算給定區塊高度處的區塊減半補貼獎勵 (BTC)。
        
        Args:
            height (int): 區塊高度。
            
        Returns:
            float: 區塊獎勵 (BTC)。
        """
        initial_reward = 50.0
        halvings = height // settings.HALVING_INTERVAL_BLOCKS
        if halvings >= 64:  # 避免位移溢出
            return 0.0
        return initial_reward / (2 ** halvings)

    def _get_hardcoded_fallback(self) -> Dict[str, Any]:
        """使用設定檔中的硬編碼提供回退數據。
        
        Returns:
            Dict[str, Any]: 回退數據字典。
        """
        logger.warning("所有即時 API 請求皆失敗。改用硬編碼回退值。")
        block_height = settings.FALLBACK_BLOCK_HEIGHT
        difficulty = settings.FALLBACK_DIFFICULTY
        hashrate_h_s = settings.FALLBACK_HASHRATE_EH * 1e18
        block_reward_btc = self._calculate_block_reward(block_height)
        
        return {
            "btc_price_usd": settings.FALLBACK_BTC_PRICE_USD,
            "difficulty": difficulty,
            "hashrate_h_s": hashrate_h_s,
            "block_height": block_height,
            "block_reward_btc": block_reward_btc,
            "est_tx_fees_btc": settings.FALLBACK_TX_FEES_BTC,
            "source": "硬編碼回退值"
        }

    def get_blockchain_data(self, force_refresh: bool = False) -> Dict[str, Any]:
        """獲取快取的區塊鏈指標或觸發 API 請求。
        
        Args:
            force_refresh (bool): 若為 True，則忽略快取並重新向 API 發送請求。
            
        Returns:
            Dict[str, Any]: 區塊鏈指標數據包。
        """
        now = time.time()
        
        # 檢查快取有效性
        if not force_refresh and self._cache and (now - self._cache_timestamp) < self.ttl:
            logger.debug("返回快取的區塊鏈指標數據")
            return self._cache

        data = None
        
        # 優先級 1: mempool.space
        data = self.fetch_mempool_space()
        
        # 優先級 2: Blockchain.com
        if not data:
            data = self.fetch_blockchain_info()
            
        # 優先級 3: CoinGecko (僅作為價格回退)
        if not data:
            data = self.fetch_coingecko()
            
        # 優先級 4: 硬編碼回退
        if not data:
            data = self._get_hardcoded_fallback()

        # 寫入時間戳記與減半指標
        data["timestamp"] = now
        
        # 計算減半倒數
        next_halving_height = ((data["block_height"] // settings.HALVING_INTERVAL_BLOCKS) + 1) * settings.HALVING_INTERVAL_BLOCKS
        blocks_remaining = next_halving_height - data["block_height"]
        
        # 估算減半時間（以每個區塊平均 600 秒計算）
        halving_countdown_time_secs = blocks_remaining * 600.0
        
        data["halving_countdown_blocks"] = blocks_remaining
        data["halving_countdown_time_secs"] = halving_countdown_time_secs

        # 更新快取
        self._cache = data
        self._cache_timestamp = now
        
        logger.info(f"成功自以下來源獲取區塊鏈數據: {data['source']}")
        return data

# 建立全局單例對象
bitcoin_api = BitcoinAPIManager()
