import streamlit as st
st.title('test_utils.py - 自動化展示')
st.info('這是從原專案腳本自動包裝產生的互動式介面。')

import pytest
import math
from utils.formatter import (
    format_currency,
    format_hashrate,
    format_probability,
    format_duration
)
from utils.logger import configure_logger

def test_format_currency() -> None:
    """Verifies that floating numbers map to currency strings correctly."""
    assert format_currency(1234.567) == "$1,234.57"
    assert format_currency(0.0) == "$0.00"
    assert format_currency(float("nan")) == "$0.00"
    assert format_currency(float("inf")) == "$0.00"

def test_format_hashrate() -> None:
    """Validates that base hashrates (H/s) are formatted to correct standard units."""
    assert format_hashrate(0) == "0 H/s"
    assert format_hashrate(-10.0) == "0 H/s"
    assert format_hashrate(500) == "500.00 H/s"
    assert format_hashrate(1500) == "1.50 KH/s"
    assert format_hashrate(1500000) == "1.50 MH/s"
    assert format_hashrate(1500000000) == "1.50 GH/s"
    assert format_hashrate(1.5e12) == "1.50 TH/s"
    assert format_hashrate(1.5e15) == "1.50 PH/s"
    assert format_hashrate(1.5e18) == "1.50 EH/s"
    # Even larger values stay at EH/s scale
    assert format_hashrate(1.5e21) == "1,500.00 EH/s"

def test_format_probability() -> None:
    """Checks float probabilities format, formatting very small values in scientific."""
    assert format_probability(0.0) == "0.00%"
    assert format_probability(-0.05) == "0.00%"
    assert format_probability(1.0) == "100.00%"
    assert format_probability(1.5) == "100.00%"
    assert format_probability(0.051234) == "5.123400000000%"
    # Small probability (e.g. 1.23 * 10^-8) -> maps to 1.23e-06%
    assert format_probability(1.23e-8, decimals=2) == "1.23e-06%"

def test_format_duration() -> None:
    """Checks seconds durations map to readable time horizons correctly."""
    assert format_duration(0.0) == "無限大"
    assert format_duration(-1.0) == "無限大"
    assert format_duration(float("inf")) == "無限大"
    
    assert format_duration(45.2) == "45.20 秒"
    assert format_duration(120) == "2 分鐘 0 秒"
    assert format_duration(3665) == "1 小時 1 分鐘"
    assert format_duration(90000) == "1 天 1 小時 0 分鐘"
    
    # Year intervals
    year_secs = 31536000.0
    assert format_duration(year_secs) == "1 年 0 天 0 小時"
    assert format_duration(12 * year_secs) == "12 年 0 天"
    
    # Millions / Billions of years
    assert format_duration(2.5e6 * year_secs) == "2.50 百萬年"
    assert format_duration(3.8e9 * year_secs) == "3.80 十億年"

def test_logger_configuration() -> None:
    """Ensures logger configuration doesn't crash on standard level hooks."""
    # This just checks that calling configure_logger executes successfully
    configure_logger(debug=True)
    configure_logger(debug=False)


# ====== 自動生成的測試執行區塊 ======
if __name__ == "__main__":
    st.write("---")
    st.subheader("函數測試區塊")
    if st.button("執行 test_format_currency"):
        try:
            res = test_format_currency() # 請視需要自行補上參數
            st.write("執行結果:", res)
        except Exception as e:
            st.error(f"執行出錯，可能需要提供參數：{e}")
    if st.button("執行 test_format_hashrate"):
        try:
            res = test_format_hashrate() # 請視需要自行補上參數
            st.write("執行結果:", res)
        except Exception as e:
            st.error(f"執行出錯，可能需要提供參數：{e}")
    if st.button("執行 test_format_probability"):
        try:
            res = test_format_probability() # 請視需要自行補上參數
            st.write("執行結果:", res)
        except Exception as e:
            st.error(f"執行出錯，可能需要提供參數：{e}")
    if st.button("執行 test_format_duration"):
        try:
            res = test_format_duration() # 請視需要自行補上參數
            st.write("執行結果:", res)
        except Exception as e:
            st.error(f"執行出錯，可能需要提供參數：{e}")
    if st.button("執行 test_logger_configuration"):
        try:
            res = test_logger_configuration() # 請視需要自行補上參數
            st.write("執行結果:", res)
        except Exception as e:
            st.error(f"執行出錯，可能需要提供參數：{e}")
