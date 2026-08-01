import streamlit as st
st.title('test_multi_stores.py - 自動化展示')
st.info('這是從原專案腳本自動包裝產生的互動式介面。')

import sys
sys.path.insert(0, ".")
import time
import logging
import pandas as pd
from core.controller import ScraperController

sys.stdout.reconfigure(encoding='utf-8')
logging.basicConfig(level=logging.INFO)

urls = [
    # 1. 元金小六鍋貼 (用戶最新指定)
    "https://www.google.com/maps/place/%E5%85%83%E9%87%91%E5%B0%8F%E5%85%AD%E9%8D%8B%E8%B2%BC/@24.1683706,120.6630758,16z/data=!4m8!3m7!1s0x3469162aceefa85f:0xd98c12588ca43b04!8m2!3d24.1683657!4d120.6656561!9m1!1b1!16s%2Fg%2F11b7tx0sfl?entry=ttu&g_ep=EgoyMDI2MDcyMi4wIKXMDSoASAFQAw%3D%3D",
    # 2. 台中文心秀泰影城
    "https://www.google.com/maps/place/%E5%8F%B0%E4%B8%AD%E6%96%87%E5%BF%83%E7%A7%80%E6%B3%B0%E5%BD%B1%E5%9F%8E/@24.1297652,120.6431849,17z/data=!4m8!3m7!1s0x34693d47f94524dd:0x507861f9b78767f8!8m2!3d24.1297603!4d120.6457652!9m1!1b1!16s%2Fg%2F11f6fzgx7k?entry=ttu&g_ep=EgoyMDI2MDcyMi4wIKXMDSoASAFQAw%3D%3D",
    # 3. 屋馬燒肉文心店
    "https://www.google.com/maps/place/%E5%B1%8B%E9%A6%AC%E7%87%92%E8%82%89%E6%96%87%E5%BF%83%E5%BA%97/@24.1510332,120.6444213,16z/data=!4m8!3m7!1s0x34693db76d585cdb:0x38eadd251bbe768!8m2!3d24.1510283!4d120.6470016!9m1!1b1!16s%2Fg%2F11c1nhh2kz?entry=ttu&g_ep=EgoyMDI2MDcyMi4wIKXMDSoASAFQAw%3D%3D"
]

st.write("=== 開始進行多店家連續自動化測試驗證 ===")
controller = ScraperController()
controller.start(urls)

while controller._is_running:
    time.sleep(1)
    while not controller._metrics_queue.empty():
        m = controller._metrics_queue.get()
        if m.get("status") in ["processing", "success", "error", "exported"]:
            st.write("進度回報:", m)

st.write("\n=== 所有店家爬取結束 ===")
st.write("總共抓取店家數:", len(controller.results))
for idx, res in enumerate(controller.results, 1):
    st.write(f"[{idx}] 店家標題: {res.title} | 成功爬取評論數: {len(res.comments)} 則")

# 驗證匯出檔案
df_comments = pd.read_csv("output/export_comments.csv")
st.write("\n匯出檔案 `output/export_comments.csv` 驗證:")
st.write("總留言筆數:", len(df_comments))
st.write("包含店家:", df_comments["post_title"].unique().tolist())
st.write("前 3 筆評論預覽:")
for _, row in df_comments.head(3).iterrows():
    st.write(f" - [{row['post_title']}] {row['author']}: {str(row['content'])[:40]}...")
