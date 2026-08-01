import streamlit as st

import os
import sys
from loguru import logger
from btc_config import settings

def configure_logger(debug: bool = False) -> None:
    """配置應用程式的 loguru 日誌記錄器。
    
    若日誌存放目錄不存在則自動建立，清除預設的 handler，
    並添加 stderr（控制台）和日誌文件輸出渠道。
    
    Args:
        debug (bool): 若為 True，則將日誌等級設為 DEBUG，否則採用 settings.LOG_LEVEL 配置。
    """
    # 移除預設的日誌 handler
    logger.remove()

    # 判定日誌等級
    log_level = "DEBUG" if debug else settings.LOG_LEVEL

    # 確保日誌存放目錄存在
    log_dir = os.path.dirname(settings.LOG_FILE_PATH)
    if log_dir and not os.path.exists(log_dir):
        st_dir = os.makedirs(log_dir, exist_ok=True)

    # 控制台輸出日誌格式
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )

    # 註冊控制台日誌輸出（Stderr）
    logger.add(
        sys.stderr,
        format=log_format,
        level=log_level,
        colorize=True
    )

    # 註冊日誌文件輸出（帶自動滾動與封存）
    try:
        logger.add(
            settings.LOG_FILE_PATH,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level=log_level,
            rotation="10 MB",
            retention="1 week",
            compression="zip",
            encoding="utf-8"
        )
    except Exception:
        pass

    logger.info(f"日誌系統初始化完成。日誌等級: {log_level}, 存檔路徑: {settings.LOG_FILE_PATH}")


# ====== 自動生成的測試執行區塊 ======
if __name__ == "__main__":
    st.write("---")
    st.subheader("函數測試區塊")
    if st.button("執行 configure_logger"):
        try:
            res = configure_logger() # 請視需要自行補上參數
            st.write("執行結果:", res)
        except Exception as e:
            st.error(f"執行出錯，可能需要提供參數：{e}")
