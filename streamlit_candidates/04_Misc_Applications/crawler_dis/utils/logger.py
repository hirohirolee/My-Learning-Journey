import streamlit as st
st.title('logger.py - 自動化展示')
st.info('這是從原專案腳本自動包裝產生的互動式介面。')

import json
import logging
import os
from logging.handlers import RotatingFileHandler


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": self.formatTime(record, self.datefmt),
            "module": record.name,
            "level": record.levelname,
            "message": record.getMessage(),
        }
        if hasattr(record, "elapsed"):
            log_data["elapsed"] = record.elapsed
        if hasattr(record, "url"):
            log_data["url"] = record.url
        if hasattr(record, "retry"):
            log_data["retry"] = record.retry
        if record.exc_info:
            log_data["exc_info"] = self.formatException(record.exc_info)

        return json.dumps(log_data, ensure_ascii=False)


def setup_logger(
    name: str = "scraper",
    log_dir: str = "logs",
    level: str = "INFO",
    rotation_size_mb: int = 10,
    rotation_count: int = 5,
) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    os.makedirs(log_dir, exist_ok=True)

    formatter = JSONFormatter()

    # Info log
    info_handler = RotatingFileHandler(
        os.path.join(log_dir, "crawler.log"),
        maxBytes=rotation_size_mb * 1024 * 1024,
        backupCount=rotation_count,
        encoding="utf-8",
    )
    info_handler.setLevel(logging.INFO)
    info_handler.setFormatter(formatter)

    # Error log
    error_handler = RotatingFileHandler(
        os.path.join(log_dir, "error.log"),
        maxBytes=rotation_size_mb * 1024 * 1024,
        backupCount=rotation_count,
        encoding="utf-8",
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)

    # Console log
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )

    logger.addHandler(info_handler)
    logger.addHandler(error_handler)
    logger.addHandler(console_handler)

    return logger


logger = setup_logger()


# ====== 自動生成的測試執行區塊 ======
if __name__ == "__main__":
    st.write("---")
    st.subheader("函數測試區塊")
    if st.button("執行 setup_logger"):
        try:
            res = setup_logger() # 請視需要自行補上參數
            st.write("執行結果:", res)
        except Exception as e:
            st.error(f"執行出錯，可能需要提供參數：{e}")
