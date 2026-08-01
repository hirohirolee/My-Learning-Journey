import streamlit as st

import argparse
from utils.logger import get_logger
from assistants.institutional_follower import InstitutionalFollower
from assistants.high_dividend_scanner import HighDividendScanner
from assistants.crash_news_monitor import CrashNewsMonitor

logger = get_logger(__name__)

def run_task(task_name: str):
    """
    3.10 Windows 工作排程器調用主程式：
    根據命令列傳入的 task_name 參數，分派並執行對應的小幫手任務。
    """
    logger.info(f"========== 啟動排程任務: {task_name} ==========")
    
    try:
        if task_name == 'institutional':
            follower = InstitutionalFollower()
            follower.scan_consecutive_buy()
            
        elif task_name == 'dividend':
            scanner = HighDividendScanner()
            # 測試用的股票清單 (包含金控、高股息ETF、電子股等)
            test_stocks = ['2884', '2892', '0056', '2330', '3231']
            scanner.scan(test_stocks)
            
        elif task_name == 'crash_monitor':
            monitor = CrashNewsMonitor()
            # 檢查台積電是否暴跌
            monitor.check_crash_and_get_news('2330')
            
        else:
            logger.error(f"未知的任務名稱: {task_name}")
            
    except Exception as e:
        logger.error(f"執行任務 {task_name} 時發生嚴重錯誤: {str(e)}", exc_info=True)
    finally:
        logger.info(f"========== 結束排程任務: {task_name} ==========\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='台股自動化監控與策略回測系統 - 排程器入口')
    parser.add_argument('--task', type=str, required=True, 
                        choices=['institutional', 'dividend', 'crash_monitor'],
                        help='指定要執行的小幫手任務名稱')
    
    args = parser.parse_args()
    run_task(args.task)
