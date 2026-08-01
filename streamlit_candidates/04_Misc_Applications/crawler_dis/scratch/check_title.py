import streamlit as st

import sys
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding='utf-8')

with open("scratch/page_text.txt", "r", encoding="utf-8") as f:
    # Let's check from our last page_text or let's run a quick evaluate on the page
    pass

# Better: let's check in the HTML content what tags contain 中興奶茶
with open("output/export.json", "r", encoding="utf-8") as f:
    pass
