import streamlit as st

import logging
from logging.handlers import RotatingFileHandler
from config import LOG_FILE

def get_logger(name: str) -> logging.Logger:
    """
    獲取設定好格式的 Logger 實例，確保系統具備完整的日誌記錄機制。
    支援寫入檔案與終端機輸出，並具備自動輪替 (Rotating) 功能。
    
    :param name: 呼叫此 Logger 的模組名稱 (通常傳入 __name__)
    :return: logging.Logger 實例
    """
    logger = logging.getLogger(name)
    
    # 避免重複添加 Handler
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # File Handler: 自動輪替，每個檔案最大 5MB，最多保留 3 個備份
        file_handler = RotatingFileHandler(
            LOG_FILE, maxBytes=5*1024*1024, backupCount=3, encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        
        # Stream Handler: 輸出到 Console 供即時查看
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
    return logger


# ====== 自動生成的測試執行區塊 ======
if __name__ == "__main__":
    st.write("---")
    st.subheader("函數測試區塊")
    if st.button("執行 get_logger"):
        try:
            res = get_logger() # 請視需要自行補上參數
            st.write("執行結果:", res)
        except Exception as e:
            st.error(f"執行出錯，可能需要提供參數：{e}")
