import streamlit as st
import streamlit.components.v1 as components

# Set page title and layout
st.set_page_config(
    page_title="十大機器學習演算法：全方位動態學習報告",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS to hide Streamlit default decorations (header, footer, padding)
hide_style = """
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .block-container {
            padding-top: 0rem !important;
            padding-bottom: 0rem !important;
            padding-left: 0rem !important;
            padding-right: 0rem !important;
        }
        iframe {
            border: none !important;
        }
    </style>
"""
st.markdown(hide_style, unsafe_allow_html=True)

import os

# Read app.html content relative to this script's directory
try:
    dir_path = os.path.dirname(os.path.realpath(__file__))
    html_path = os.path.join(dir_path, "app.html")
    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    
    # Embed the HTML single-page app
    components.html(html_content, height=1450, scrolling=True)
except FileNotFoundError:
    st.error("找不到 app.html 檔案，請確認與 app.py 放在同個資料夾。")

