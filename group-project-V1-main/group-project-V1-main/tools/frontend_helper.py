"""
frontend_helper.py
─────────────────────────────────────────────────────────────────────────────
中端專屬前端視覺化輔助工具（Streamlit 對接外掛）
─────────────────────────────────────────────────────────────────────────────
"""

import streamlit as st
import pandas as pd

def render_midend_dashboard(analysis_data: dict):
    """
    接收中端分析出的多維數據，並自動在 Streamlit 渲染出華麗的圖表
    """
    if not analysis_data:
        st.warning("⚠️ 尚無中端分析數據")
        return

    st.markdown("### 📊 中端智慧輿情指標")
    
    # 1. 建立儀表看板區塊
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="🚨 危機範疇", value=analysis_data.get("reviews_tag", "未分類"))
    with col2:
        st.metric(label="🛡️ 風險層級", value=analysis_data.get("risk_level", "正常無虞"))
    with col3:
        risk_pct = int(analysis_data.get("risk_score", 0) * 100)
        st.metric(label="📈 危機機率", value=f"{risk_pct}%")

    st.markdown("---")
    
    # 2. 情感維度視覺化（長條圖）
    st.markdown("#### 😡 消費者多維情緒分佈")
    chart_df = pd.DataFrame({
        '情緒指標': ['憤怒值', '失望值', '喜悅值'],
        '分數 (0-100)': [
            analysis_data.get("emotion_anger", 0), 
            analysis_data.get("emotion_disappointment", 0), 
            analysis_data.get("emotion_joy", 0)
        ]
    })
    
    st.bar_chart(chart_df, x='情緒指標', y='分數 (0-100)', use_container_width=True)