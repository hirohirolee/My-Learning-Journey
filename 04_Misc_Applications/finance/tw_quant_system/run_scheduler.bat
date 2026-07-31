@echo off
chcp 65001
REM ========================================================
REM 台股小幫手 Windows 工作排程器啟動腳本 (Chapter 3.10)
REM 
REM 部署說明：
REM 1. 打開 Windows「工作排程器」(Task Scheduler)
REM 2. 建立基本工作，設定每日觸發時間 (例如 14:00 盤後)
REM 3. 動作選擇「啟動程式」，指向此 .bat 檔案
REM ========================================================

echo ==============================================
echo 正在啟動台股量化小幫手排程...
echo 執行時間：%date% %time%
echo ==============================================

REM 步驟1：切換到專案目錄 (依據實際路徑調整)
cd /d "%~dp0"

REM 步驟2：執行虛擬環境 (如果有的話)
REM call venv\Scripts\activate

REM 步驟3：依序啟動各個小幫手
echo [1/3] 執行法人追蹤小幫手...
python main_scheduler.py --task institutional

echo [2/3] 執行高殖利率掃描小幫手...
python main_scheduler.py --task dividend

echo [3/3] 執行暴跌與消息監控...
python main_scheduler.py --task crash_monitor

echo ==============================================
echo 任務執行完畢，請查看 logs/system.log 確認結果。
echo ==============================================
pause
