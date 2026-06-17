# -*- coding: utf-8 -*-
"""
ESG 永續報告書自動化生成系統 - Web Dashboard 主入口 (極簡模組化版)
"""

import sys

# 解決 Windows 環境下 cp950 無法編碼 Unicode 字符（如 Emojis）的錯誤
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
if hasattr(sys.stderr, 'reconfigure'):
    try:
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

import streamlit as st
import os
from modules.data_processor import ESGDataProcessor
from modules.local_ai_manager import ESGLLMManager
from modules.report_builder import ESGReportBuilder
import config
from gri_config import GRI_CONFIG
from ui_components import (
    render_sidebar_config,
    render_data_upload_tabs,
    render_indicator_checklist,
    render_report_preview_and_download
)

# 設定網頁資訊與主題
st.set_page_config(
    page_title="ESG 永續報告書自動化生成系統",
    layout="wide",
    page_icon="🌱",
    initial_sidebar_state="expanded"
)

# 注入高質感企業識別 CSS 樣式
st.markdown("""
    <style>
    .main {
        background-color: #FAFAFA;
    }
    h1, h2, h3 {
        font-family: 'Microsoft JhengHei', sans-serif;
    }
    /* 漸層標題橫幅 */
    .banner {
        background: linear-gradient(135deg, #2E7D32 0%, #1565C0 100%);
        padding: 30px;
        border-radius: 12px;
        color: white;
        margin-bottom: 25px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .banner h1 {
        margin: 0;
        font-size: 2.3rem;
        font-weight: 700;
    }
    .banner p {
        margin: 8px 0 0 0;
        font-size: 1.1rem;
        opacity: 0.95;
    }
    /* 卡片包裝 */
    .card {
        background-color: white;
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin-bottom: 20px;
        border-left: 5px solid #2E7D32;
    }
    </style>
""", unsafe_allow_html=True)

# 頂部漸層標題橫幅
st.markdown("""
    <div class="banner">
        <h1>🌱 ESG 永續報告書自動化生成系統</h1>
        <p>提供企業各部門數據上傳，調度地端安全 AI 生產合規文本，結合數據圖表，一鍵封裝 Word (.docx) 報告書初稿。</p>
    </div>
""", unsafe_allow_html=True)

# 1. 渲染側邊欄設定
sidebar_data = render_sidebar_config()

# 2. 渲染主畫面雙欄佈局
col1, col2 = st.columns([1, 1])

with col1:
    render_data_upload_tabs()

with col2:
    selected_indicators, selected_subchapters, target_words = render_indicator_checklist()
    st.write("---")
    generate_btn = st.button("🚀 開始地端安全生成完整報告書", use_container_width=True, type="primary")

# 3. 執行生成邏輯
if generate_btn:
    if not selected_indicators:
        st.warning("⚠️ 請至少選擇一個 GRI 揭露指標！")
        st.stop()
        
    for ch_code in selected_indicators:
        if not selected_subchapters[ch_code]:
            st.error(f"❌ 您啟用了 {GRI_CONFIG[ch_code]['name']} 指標，但未勾選任何細部子項目。請勾選至少一個子項目！")
            st.stop()
        
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    chapters_data = {}
    ai_manager = ESGLLMManager(model_name=sidebar_data["model_name"], host=sidebar_data["ollama_host"])
    processor = ESGDataProcessor()
    
    try:
        # ------------ 步驟一：數據解析 ------------
        status_text.write("⏳ [1/3] 正在解析與清洗各部門上傳的 Excel 數據...")
        progress_bar.progress(20)
        
        for ch_code in selected_indicators:
            cfg = GRI_CONFIG[ch_code]
            file_data = st.session_state.get(f"stored_{cfg['file_key']}")
            processor_method = getattr(processor, cfg["processor_method"])
            
            if cfg["baseline_required"]:
                parsed_data = processor_method(
                    file_data, 
                    company_name=sidebar_data["company_name"], 
                    reporting_year=sidebar_data["reporting_year"],
                    baseline_emissions=sidebar_data["baseline_input"]
                )
            else:
                parsed_data = processor_method(
                    file_data, 
                    company_name=sidebar_data["company_name"], 
                    reporting_year=sidebar_data["reporting_year"]
                )
            chapters_data[ch_code] = parsed_data
            
        # ------------ 步驟二：AI 生成文本 ------------
        status_text.write("⏳ [2/3] 正在調度地端 Ollama AI 進行各細項子章節獨立寫作...")
        progress_bar.progress(50)
        
        for ch_code in selected_indicators:
            st.write(f"📝 正在撰寫：{ch_code} (依勾選項目生成)...")
            sub_chapters = ai_manager.generate_chapter_subsections(
                chapters_data[ch_code], 
                ch_code, 
                target_words=target_words,
                selected_subs=selected_subchapters[ch_code]
            )
            chapters_data[ch_code]["sub_chapters"] = sub_chapters
            chapters_data[ch_code]["ai_text"] = "\n\n".join(sub_chapters.values())
            
        # ------------ 步驟三：圖表繪製與 Word 封裝 ------------
        status_text.write("⏳ [3/3] 正在繪製統計圖表並進行 Word 文件組裝...")
        progress_bar.progress(80)
        
        builder = ESGReportBuilder()
        output_filepath = builder.build_full_report(sidebar_data["company_name"], sidebar_data["reporting_year"], chapters_data)
        
        progress_bar.progress(100)
        status_text.success("🎉 永續報告書初稿生成成功！")
        
        # 4. 渲染預覽與下載
        render_report_preview_and_download(output_filepath, chapters_data, selected_indicators)
                
    except Exception as e:
        status_text.empty()
        progress_bar.empty()
        st.error(f"❌ 報告書生成失敗！錯誤原因：{str(e)}")
