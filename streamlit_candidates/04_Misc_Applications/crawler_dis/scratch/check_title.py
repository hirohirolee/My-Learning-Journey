import streamlit as st
st.title('check_title.py - 自動化展示')
st.info('這是從原專案腳本自動包裝產生的互動式介面。')

import sys
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding='utf-8')

with open("scratch/page_text.txt", "r", encoding="utf-8") as f:
    # Let's check from our last page_text or let's run a quick evaluate on the page
    pass

# Better: let's check in the HTML content what tags contain 中興奶茶
with open("output/export.json", "r", encoding="utf-8") as f:
    pass
