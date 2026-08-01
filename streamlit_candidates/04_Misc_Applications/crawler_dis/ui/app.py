import os
import sys
import time

import pandas as pd
import streamlit as st

sys.modules.pop('config', None)
# Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    import psutil
except ImportError:
    psutil = None

from core.controller import ScraperController

st.set_page_config(page_title="Cross-Forum Scraper", layout="wide")
st.title("跨論壇留言爬蟲系統")

if "controller" not in st.session_state:
    st.session_state.controller = ScraperController()

if "logs" not in st.session_state:
    st.session_state.logs = []

controller = st.session_state.controller

# Sidebar config
st.sidebar.header("設定")
urls_input = st.sidebar.text_area(
    "輸入 URLs (每行一個)",
    "https://www.ptt.cc/bbs/Gossiping/M.1706151234.A.123.html\nhttps://www.dcard.tw/f/mood/p/254477889",
)

col1, col2, col3 = st.sidebar.columns(3)
with col1:
    if st.button("啟動", disabled=controller.is_running):
        urls = [u.strip() for u in urls_input.split("\n") if u.strip()]
        if urls:
            controller.start(urls)
            st.session_state.logs = []
            st.rerun()
with col2:
    if st.button("暫停/恢復", disabled=not controller.is_running):
        if controller.cancellation_token.is_paused:
            controller.resume()
        else:
            controller.pause()
        st.rerun()
with col3:
    if st.button("停止", disabled=not controller.is_running):
        controller.stop()
        st.rerun()

# Main Area
st.header("監控面板")

metrics_col1, metrics_col2, metrics_col3 = st.columns(3)

status_text = "執行中" if controller.is_running else "已停止"
if controller.is_running and controller.cancellation_token.is_paused:
    status_text = "已暫停"

metrics_col1.metric("狀態", status_text)
mem_val = f"{psutil.virtual_memory().percent}%" if psutil else "正常"
cpu_val = f"{psutil.cpu_percent()}%" if psutil else "正常"
metrics_col2.metric("記憶體使用率", mem_val)
metrics_col3.metric("CPU 使用率", cpu_val)

# Metrics polling
if controller.is_running:
    metrics = controller.get_metrics()
    for m in metrics:
        st.session_state.logs.insert(0, m)
        if len(st.session_state.logs) > 100:
            st.session_state.logs.pop()

    # Auto-refresh
    time.sleep(1)
    st.rerun()

st.subheader("處理日誌")
if st.session_state.logs:
    log_df = pd.DataFrame(st.session_state.logs)
    st.dataframe(log_df, width="stretch")
else:
    st.info("尚無日誌")

# Data Preview
st.subheader("匯出預覽與歷史檔案")
comments_csv_path = os.path.join("output", "export_comments.csv")
csv_path = os.path.join("output", "export.csv")

if os.path.exists(comments_csv_path):
    st.markdown("### 📝 最新一次爬取留言明細 (`export_comments.csv`)")
    try:
        cdf = pd.read_csv(comments_csv_path)
        st.dataframe(cdf.head(100), width="stretch")
    except Exception:
        st.error("無法讀取留言 CSV (可能正在寫入)")

if os.path.exists(csv_path):
    st.markdown("### 📌 最新一次爬取景點摘要 (`export.csv`)")
    try:
        df = pd.read_csv(csv_path)
        st.dataframe(df.head(50), width="stretch")
    except Exception:
        st.error("無法讀取 CSV (可能正在寫入)")
elif not os.path.exists(comments_csv_path):
    st.info("尚無最新匯出資料")

# Historical Files Section
if os.path.exists("output"):
    st.markdown("---")
    st.markdown("### 📂 歷史匯出 Excel 表格與 CSV 檔案 (永久保存，不再被覆蓋)")
    try:
        files_info = []
        for fname in os.listdir("output"):
            fpath = os.path.join("output", fname)
            if os.path.isfile(fpath) and (fname.endswith(".xlsx") or fname.endswith(".csv")):
                mtime = os.path.getmtime(fpath)
                size_kb = round(os.path.getsize(fpath) / 1024, 2)
                from datetime import datetime
                time_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
                files_info.append({
                    "檔案名稱": fname,
                    "檔案大小 (KB)": size_kb,
                    "建立/修改時間": time_str,
                    "檔案格式": "Excel 表格" if fname.endswith(".xlsx") else "CSV 資料表"
                })
        if files_info:
            files_df = pd.DataFrame(files_info).sort_values(by="建立/修改時間", ascending=False)
            st.dataframe(files_df, width="stretch", hide_index=True)
    except Exception as e:
        st.error(f"讀取歷史檔案列表時出錯: {e}")

