# -*- coding: utf-8 -*-
"""
ESG 永續報告書自動化生成系統 - Streamlit 可複用 UI 元件模組
"""

import os
from typing import Dict, Any, List, Tuple
import streamlit as st
import config
from gri_config import GRI_CONFIG
from templates import get_excel_template_bytes
from modules.local_ai_manager import ESGLLMManager

def render_sidebar_config() -> Dict[str, Any]:
    """
    於側邊欄渲染報告的基礎設定（企業名稱、報告年度、基準年排放量）與地端 Ollama AI 設定，
    並即時顯示地端 AI 連線狀態與模型下載狀態。
    
    Returns:
        包含設定資料的字典：
        {
            "company_name": str,
            "reporting_year": str,
            "baseline_input": float,
            "ollama_host": str,
            "model_name": str
        }
    """
    st.sidebar.markdown("### ⚙️ 報告設定與環境配置")

    company_name: str = st.sidebar.text_input("企業名稱", value="星光電子製造廠")
    reporting_year: str = st.sidebar.text_input("報告年度", value="2025")
    baseline_input: float = st.sidebar.number_input("基準年總排放量 (tCO2e，計算 YoY 減碳比例)", value=3571.5, step=10.0)

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🤖 地端 AI 設定 (Ollama)")
    ollama_host: str = st.sidebar.text_input("Ollama 伺服器網址", value=config.OLLAMA_HOST)
    model_name: str = st.sidebar.selectbox("Ollama 模型選擇", options=["llama3", "llama3.1", "yenting/llama3-taide", "custom"])
    if model_name == "custom":
        model_name = st.sidebar.text_input("請輸入自訂模型代碼", value="llama3")

    # Ollama 連線與模型下載狀態預檢
    is_connected, model_downloaded, installed_models = ESGLLMManager.check_connection(ollama_host, model_name)

    if is_connected:
        if model_downloaded:
            st.sidebar.success("🟢 連線成功 (模型已就緒)")
        else:
            st.sidebar.warning(f"⚠️ 連線成功，但模型 '{model_name}' 未下載 (將啟用地端備用文本)")
            if installed_models:
                st.sidebar.info(f"本地現有模型: {', '.join(installed_models)}")
    else:
        st.sidebar.error("🔴 無法連線至 Ollama (將啟用地端高階備用文本)")
        
    return {
        "company_name": company_name,
        "reporting_year": reporting_year,
        "baseline_input": baseline_input,
        "ollama_host": ollama_host,
        "model_name": model_name
    }

def render_data_upload_tabs() -> None:
    """
    渲染 Excel 模板下載按鈕與資料上傳欄位，並將上傳的二進位內容儲存至 st.session_state 以利跨元件狀態持久化。
    """
    st.markdown('<div class="card"><h3>📥 數據上傳與模板下載</h3></div>', unsafe_allow_html=True)
    st.write("您可以下載標準範本，或直接上傳您企業的數據表格。未上傳者將啟用預設模擬數據。")
    
    tabs = st.tabs(["🍀 GRI 305 & 404", "⚡ GRI 302 & 306", "👥 GRI 401 & 405", "💼 經濟與治理"])
    
    for i, tab in enumerate(tabs):
        with tab:
            # 篩選出屬於該 Tab 索引的指標設定
            tab_indicators = [cfg for cfg in GRI_CONFIG.values() if cfg["tab_index"] == i]
            
            # 使用 columns 平行排列下載與上傳按鈕
            cols = st.columns(len(tab_indicators))
            for col, cfg in zip(cols, tab_indicators):
                with col:
                    st.markdown(f"**{cfg['name']}**")
                    
                    # 下載模板按鈕，讀取 templates.py 內 cache 的 bytes 資料
                    st.download_button(
                        label="📊 下載模板檔案 (.xlsx)",
                        data=get_excel_template_bytes(cfg["template_key"]),
                        file_name=cfg["template_key"] + "_template.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key=f"download_{cfg['template_key']}"
                    )
                    
                    # 上傳檔案
                    file_key = cfg["file_key"]
                    uploaded_file = st.file_uploader(
                        f"上傳 {cfg['code']} 數據 Excel", 
                        type=["xlsx"], 
                        key=f"uploader_{file_key}"
                    )
                    
                    state_key = f"stored_{file_key}"
                    if state_key not in st.session_state:
                        st.session_state[state_key] = None
                    if uploaded_file is not None:
                        st.session_state[state_key] = uploaded_file.getvalue()
                        
                    # 若 session_state 中有已載入檔案，顯示綠色狀態資訊
                    if st.session_state.get(state_key) is not None:
                        st.success(f"🟢 已載入上傳的 {cfg['code']} 數據")

def render_indicator_checklist() -> Tuple[List[str], Dict[str, List[str]], int]:
    """
    於介面渲染可供勾選的 GRI 揭露指標與細部子項目，並提供單一子章節 AI 寫作字數滑桿設定。
    
    Returns:
        包含選取的指標清單、各指標所勾選的子項目字典，以及目標字數設定的三元組：
        (selected_indicators, selected_subchapters, target_words)
    """
    st.markdown('<div class="card"><h3>📑 揭露指標設定</h3></div>', unsafe_allow_html=True)
    st.write("請勾選要導入報告書之 GRI 揭露指標與細部子項目：")
    
    categories = [
        {"title": "🍀 環境面 (GRI 300 系列) 指標目錄", "prefix_list": ["302", "305", "306"]},
        {"title": "👥 社會面 (GRI 400 系列) 指標目錄", "prefix_list": ["401", "404", "405"]},
        {"title": "💼 治理與經濟面 (GRI 200 & 2 系列) 指標目錄", "prefix_list": ["201", "205", "2"]}
    ]
    
    selected_indicators: List[str] = []
    selected_subchapters: Dict[str, List[str]] = {}
    
    for cat in categories:
        with st.expander(cat["title"], expanded=True):
            # 依照定義的 prefix 渲染指標
            for key, cfg in GRI_CONFIG.items():
                if cfg["code"] in cat["prefix_list"]:
                    is_active = st.checkbox(
                        cfg["name"], 
                        value=(cfg["code"] in ["305", "404"]), 
                        help=cfg["help"], 
                        key=f"active_{cfg['code']}"
                    )
                    if is_active:
                        selected_indicators.append(key)
                        selected_subchapters[key] = []
                        
                        c1, c2 = st.columns([0.08, 0.92])
                        with c2:
                            for sub_id, sub_info in cfg["sub_items"].items():
                                if st.checkbox(sub_info["label"], value=sub_info["default"], key=f"sub_{sub_id}"):
                                    selected_subchapters[key].append(sub_id)
                                    
    target_words: int = st.slider(
        "每項細部子章節 AI 寫作字數", 
        min_value=150, 
        max_value=600, 
        value=350, 
        step=50, 
        help="決定地端 AI 撰寫各子細項時的描述長度。"
    )
    
    st.info(
        "💡 **安全合規說明**：本系統所有 AI 文本擴寫與計算，均在您的地端設備 (Localhost Ollama) 完成。 "
        "沒有任何商業機密數據會上傳至第三方公有雲端，符合最嚴格的企業資訊安全稽核要求。"
    )
    
    return selected_indicators, selected_subchapters, target_words

def render_report_preview_and_download(docx_filepath: str, chapters_data: Dict[str, Any], selected_indicators: List[str]) -> None:
    """
    提供一鍵下載完整 Word 報告書之按鈕，並渲染各指標 AI 生成描述文本之即時預覽區。
    
    Args:
        docx_filepath: Word 文件之本機路徑
        chapters_data: 各指標之結構化資料
        selected_indicators: 使用者選取的指標列表
    """
    st.balloons()
    st.write("---")
    st.markdown("### 📂 報告書生成成果與下載")
    
    with open(docx_filepath, "rb") as f:
        docx_bytes = f.read()
        
    filename = os.path.basename(docx_filepath)
    
    st.download_button(
        label="💾 一鍵下載完整 Word 報告書 (.docx)",
        data=docx_bytes,
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        use_container_width=True
    )
    
    # 預覽區
    st.markdown("### 🔍 AI 生成文本即時預覽")
    for ch_code in selected_indicators:
        with st.expander(f"👁️ 預覽 {ch_code} 生成描述"):
            for sub_id, text in chapters_data[ch_code].get("sub_chapters", {}).items():
                st.markdown(f"**子章節 {sub_id}**")
                st.info(text)
