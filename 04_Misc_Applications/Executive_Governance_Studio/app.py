"""Standalone launcher for the Executive Governance Studio.

Usage (from this folder):
    streamlit run app.py

The same page scripts are also mounted by the root ``Home.py`` portfolio router,
using identical url paths so links behave the same in both modes.
"""

import streamlit as st

st.set_page_config(
    page_title="Executive Governance Studio | Hiro Lee",
    page_icon="🏛️",
    layout="wide",
)

pages = {
    "🏛️ Executive Governance Studio": [
        st.Page("cbam_calculator.py", title="EU CBAM 碳關稅財務衝擊試算", icon="⚖️", url_path="esg-cbam-calculator", default=True),
        st.Page("ai_act_scanner.py", title="EU AI Act 風險分級掃描器", icon="🛡️", url_path="ai-act-scanner"),
        st.Page("ai_security_scanner.py", title="AI 系統資安與護欄檢測沙盒", icon="🔒", url_path="ai-security-scanner"),
        st.Page("iso27001_radar.py", title="ISO 27001:2022 成熟度雷達", icon="🎯", url_path="iso-27001-radar"),
    ]
}

st.navigation(pages).run()
