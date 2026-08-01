import streamlit as st

import pytest
from unittest.mock import patch, MagicMock
import time
from core.bitcoin_api import BitcoinAPIManager, bitcoin_api

@pytest.fixture
def api_manager() -> BitcoinAPIManager:
    """Provides a fresh instance of BitcoinAPIManager for testing."""
    return BitcoinAPIManager()

def test_calculate_block_reward(api_manager: BitcoinAPIManager) -> None:
    """Verifies calculated block rewards at standard halving block heights."""
    # Subsidy halving milestones:
    # 0 to 209,999: 50 BTC
    # 210,000 to 419,999: 25 BTC
    # 420,000 to 629,999: 12.5 BTC
    # 630,000 to 839,999: 6.25 BTC
    # 840,000 to 1,049,999: 3.125 BTC
    assert api_manager._calculate_block_reward(100000) == 50.0
    assert api_manager._calculate_block_reward(210000) == 25.0
    assert api_manager._calculate_block_reward(420000) == 12.5
    assert api_manager._calculate_block_reward(630000) == 6.25
    assert api_manager._calculate_block_reward(840000) == 3.125

@patch("core.bitcoin_api.requests.get")
def test_fetch_mempool_space_success(mock_get: MagicMock, api_manager: BitcoinAPIManager) -> None:
    """Verifies that mempool.space parsing succeeds on mock JSON payloads."""
    # Define mocks for prices, block tip height, and block detail endpoints
    mock_price_res = MagicMock()
    mock_price_res.status_code = 200
    mock_price_res.json.return_value = {"USD": 96500.0}

    mock_height_res = MagicMock()
    mock_height_res.status_code = 200
    mock_height_res.text = "852300"

    mock_blocks_res = MagicMock()
    mock_blocks_res.status_code = 200
    mock_blocks_res.json.return_value = [
        {
            "height": 852300,
            "difficulty": 91_500_000_000_000.0,
            "extras": {
                "reward": 312500000,       # in Satoshis (3.125 BTC)
                "totalFees": 25000000,     # in Satoshis (0.25 BTC)
            }
        }
    ]

    # Map side_effect of requests.get calls
    mock_get.side_effect = [mock_price_res, mock_height_res, mock_blocks_res]

    data = api_manager.fetch_mempool_space()
    
    assert data is not None
    assert data["btc_price_usd"] == 96500.0
    assert data["block_height"] == 852300
    assert data["difficulty"] == 91_500_000_000_000.0
    assert data["block_reward_btc"] == 3.125
    assert data["est_tx_fees_btc"] == 0.25
    assert data["source"] == "mempool.space"

@patch("core.bitcoin_api.requests.get")
def test_fetch_blockchain_info_success(mock_get: MagicMock, api_manager: BitcoinAPIManager) -> None:
    """Verifies that Blockchain.com endpoint maps successfully on mock inputs."""
    mock_price = MagicMock()
    mock_price.status_code = 200
    mock_price.json.return_value = {"USD": {"last": 95000.0}}

    mock_height = MagicMock()
    mock_height.status_code = 200
    mock_height.text = "850000"

    mock_diff = MagicMock()
    mock_diff.status_code = 200
    mock_diff.text = "90000000000000.0"

    mock_hr = MagicMock()
    mock_hr.status_code = 200
    mock_hr.text = "650000000.0" # hashrate in GH/s

    mock_get.side_effect = [mock_price, mock_height, mock_diff, mock_hr]

    data = api_manager.fetch_blockchain_info()
    
    assert data is not None
    assert data["btc_price_usd"] == 95000.0
    assert data["block_height"] == 850000
    assert data["difficulty"] == 90_000_000_000_000.0
    assert data["hashrate_h_s"] == 6.5e17 # Convert GH/s to H/s
    assert data["source"] == "Blockchain.com"

@patch("core.bitcoin_api.requests.get")
def test_coingecko_price_fallback(mock_get: MagicMock, api_manager: BitcoinAPIManager) -> None:
    """Tests CoinGecko price resolution fallback."""
    mock_price = MagicMock()
    mock_price.status_code = 200
    mock_price.json.return_value = {"bitcoin": {"usd": 94000.0}}

    mock_get.return_value = mock_price

    data = api_manager.fetch_coingecko()
    
    assert data is not None
    assert data["btc_price_usd"] == 94000.0
    assert data["source"] == "CoinGecko"

@patch("core.bitcoin_api.requests.get")
def test_caching_and_refresh_behavior(mock_get: MagicMock, api_manager: BitcoinAPIManager) -> None:
    """Verifies that the manager caches state and only repeats request if forced or expired."""
    mock_res = MagicMock()
    mock_res.status_code = 200
    mock_res.json.return_value = {"USD": 95000.0}
    
    # We mock only the price endpoint for simplicity, making subsequent calls return cache
    mock_get.return_value = mock_res
    
    # Mock mempool.space internal call directly to control output
    api_manager.fetch_mempool_space = MagicMock(return_value={
        "btc_price_usd": 95000.0,
        "difficulty": 90e12,
        "hashrate_h_s": 6.5e17,
        "block_height": 850000,
        "block_reward_btc": 3.125,
        "est_tx_fees_btc": 0.15,
        "source": "mempool.space"
    })
    
    # First call
    data1 = api_manager.get_blockchain_data()
    # Second call
    data2 = api_manager.get_blockchain_data()
    
    # Check that it returned the same data
    assert data1 == data2
    # Verify fetch method was called exactly once due to caching
    api_manager.fetch_mempool_space.assert_called_once()
    
    # Call with force refresh
    data3 = api_manager.get_blockchain_data(force_refresh=True)
    assert api_manager.fetch_mempool_space.call_count == 2

@patch("core.bitcoin_api.requests.get")
def test_all_apis_fail_trigger_fallback(mock_get: MagicMock, api_manager: BitcoinAPIManager) -> None:
    """Verifies fallback values are returned when all endpoint requests raise HTTP errors."""
    mock_res = MagicMock()
    mock_res.status_code = 500  # Return error codes
    mock_get.return_value = mock_res

    # This will trigger mempool.space, Blockchain.com, CoinGecko failures
    # and return hardcoded fallback configuration.
    data = api_manager.get_blockchain_data(force_refresh=True)
    assert data is not None
    assert data["btc_price_usd"] == 95000.0
    assert data["source"] == "硬編碼回退值"
    assert data["halving_countdown_blocks"] > 0


# ====== 自動生成的測試執行區塊 ======
if __name__ == "__main__":
    st.write("---")
    st.subheader("函數測試區塊")
    if st.button("執行 api_manager"):
        try:
            res = api_manager() # 請視需要自行補上參數
            st.write("執行結果:", res)
        except Exception as e:
            st.error(f"執行出錯，可能需要提供參數：{e}")
    if st.button("執行 test_calculate_block_reward"):
        try:
            res = test_calculate_block_reward() # 請視需要自行補上參數
            st.write("執行結果:", res)
        except Exception as e:
            st.error(f"執行出錯，可能需要提供參數：{e}")
    if st.button("執行 test_fetch_mempool_space_success"):
        try:
            res = test_fetch_mempool_space_success() # 請視需要自行補上參數
            st.write("執行結果:", res)
        except Exception as e:
            st.error(f"執行出錯，可能需要提供參數：{e}")
    if st.button("執行 test_fetch_blockchain_info_success"):
        try:
            res = test_fetch_blockchain_info_success() # 請視需要自行補上參數
            st.write("執行結果:", res)
        except Exception as e:
            st.error(f"執行出錯，可能需要提供參數：{e}")
    if st.button("執行 test_coingecko_price_fallback"):
        try:
            res = test_coingecko_price_fallback() # 請視需要自行補上參數
            st.write("執行結果:", res)
        except Exception as e:
            st.error(f"執行出錯，可能需要提供參數：{e}")
    if st.button("執行 test_caching_and_refresh_behavior"):
        try:
            res = test_caching_and_refresh_behavior() # 請視需要自行補上參數
            st.write("執行結果:", res)
        except Exception as e:
            st.error(f"執行出錯，可能需要提供參數：{e}")
    if st.button("執行 test_all_apis_fail_trigger_fallback"):
        try:
            res = test_all_apis_fail_trigger_fallback() # 請視需要自行補上參數
            st.write("執行結果:", res)
        except Exception as e:
            st.error(f"執行出錯，可能需要提供參數：{e}")
