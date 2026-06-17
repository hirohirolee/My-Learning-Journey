# -*- coding: utf-8 -*-
"""
ESG 永續報告書自動化生成系統 - Web Dashboard 介面
"""

import streamlit as st
import os
import pandas as pd
import io
import time
from modules.data_processor import ESGDataProcessor
from modules.local_ai_manager import ESGLLMManager
from modules.report_builder import ESGReportBuilder
import config

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

# ----------------- 輔助函數：動態產出 Excel 模板二進位 -----------------
def generate_env_template():
    """產出環境指標 Excel 二進位資料"""
    df = pd.DataFrame([
        {"排放源別": "範疇一 (直接)", "排放源名稱": "柴油發電機", "碳排放量_噸": 150.5},
        {"排放源別": "範疇一 (直接)", "排放源名稱": "冷媒逸散", "碳排放量_噸": 45.2},
        {"排放源別": "範疇二 (間接)", "排放源名稱": "外購電力", "碳排放量_噸": 3250.8}
    ])
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name="Emissions Data")
    return output.getvalue()

def generate_soc_template():
    """產出人資指標 Excel 二進位資料"""
    df = pd.DataFrame([
        {"指標分類": "培訓時數", "指標名稱": "高階主管平均培訓時數", "數值": 45.0, "單位": "小時"},
        {"指標分類": "培訓時數", "指標名稱": "中階主管平均培訓時數", "數值": 32.5, "單位": "小時"},
        {"指標分類": "培訓時數", "指標名稱": "基層員工平均培訓時數", "數值": 28.0, "單位": "小時"},
        {"指標分類": "培訓時數", "指標名稱": "男性員工平均培訓時數", "數值": 29.5, "單位": "小時"},
        {"指標分類": "培訓時數", "指標名稱": "女性員工平均培訓時數", "數值": 31.0, "單位": "小時"},
        {"指標分類": "培訓時數", "指標名稱": "全體員工平均培訓時數", "數值": 30.2, "單位": "小時"},
        {"指標分類": "離職率", "指標名稱": "新進員工比率", "數值": 12.5, "單位": "%"},
        {"指標分類": "離職率", "指標名稱": "員工離職率", "數值": 8.4, "單位": "%"}
    ])
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name="HR Training & Turnover")
    return output.getvalue()

# ----------------- 網頁主介面渲染 -----------------

# 頂部漸層標題橫幅
st.markdown("""
    <div class="banner">
        <h1>🌱 ESG 永續報告書自動化生成系統</h1>
        <p>提供企業各部門數據上傳，調度地端安全 AI 生產合規文本，結合數據圖表，一鍵封裝 Word (.docx) 報告書初稿。</p>
    </div>
""", unsafe_allow_html=True)

# 側邊欄設定區
st.sidebar.markdown("### ⚙️ 報告設定與環境配置")

company_name = st.sidebar.text_input("企業名稱", value="星光電子製造廠")
reporting_year = st.sidebar.text_input("報告年度", value="2025")
baseline_input = st.sidebar.number_input("基準年總排放量 (tCO2e，計算 YoY 減碳比例)", value=3571.5, step=10.0)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🤖 地端 AI 設定 (Ollama)")
ollama_host = st.sidebar.text_input("Ollama 伺服器網址", value=config.OLLAMA_HOST)
model_name = st.sidebar.selectbox("Ollama 模型選擇", options=["llama3", "llama3.1", "yenting/llama3-taide", "custom"])
if model_name == "custom":
    model_name = st.sidebar.text_input("請輸入自訂模型代碼", value="llama3")

# 主畫面佈局
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown('<div class="card"><h3>📥 數據上傳區與模板下載</h3></div>', unsafe_allow_html=True)
    
    # 模板下載按鈕
    st.write("測試前可先下載下方標準 Excel 數據模板：")
    t_col1, t_col2 = st.columns(2)
    with t_col1:
        st.download_button(
            label="📊 下載環境數據模板 (.xlsx)",
            data=generate_env_template(),
            file_name="GRI_305_環境數據模板.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    with t_col2:
        st.download_button(
            label="👥 下載人資數據模板 (.xlsx)",
            data=generate_soc_template(),
            file_name="GRI_404_人資數據模板.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
    st.write("")
    
    # 拖放上傳區
    env_file = st.file_uploader("上傳環境數據 Excel (預期含: 排放源別、排放源名稱、碳排放量_噸)", type=["xlsx"])
    soc_file = st.file_uploader("上傳人資數據 Excel (預期含: 指標分類、指標名稱、數值、單位)", type=["xlsx"])

with col2:
    st.markdown('<div class="card"><h3>📑 揭露指標設定</h3></div>', unsafe_allow_html=True)
    
    st.write("請勾選要導入報告書之 GRI 揭露指標與細部子項目：")
    selected_indicators = []
    
    # 分類一：環境面
    with st.expander("🍀 環境面 (GRI 300 系列) 指標目錄", expanded=True):
        gri_305_active = st.checkbox("GRI 305: 溫室氣體排放 (Emissions)", value=True, help="統計範疇一與範疇二碳排放")
        selected_sub_305 = []
        if gri_305_active:
            selected_indicators.append("GRI 305")
            c1, c2 = st.columns([0.08, 0.92])
            with c2:
                if st.checkbox("├─ 3.1.1 範疇一（直接排放）來源與數據解讀", value=True):
                    selected_sub_305.append("3.1.1")
                if st.checkbox("├─ 3.1.2 範疇二（間接排放）電力分析與路徑", value=True):
                    selected_sub_305.append("3.1.2")
                if st.checkbox("└─ 3.1.3 年度排放變動率（YoY）與成效評估", value=True):
                    selected_sub_305.append("3.1.3")
                    
        if st.checkbox("GRI 302: 能源消耗 (Energy) [擴充功能]", value=False, help="統計柴油、電力等能源耗用與能效分析"):
            selected_indicators.append("GRI 302")
        if st.checkbox("GRI 306: 廢棄物與回收 (Waste) [擴充功能]", value=False, help="統計廢棄物產生與流向管理"):
            selected_indicators.append("GRI 306")
            
    # 分類二：社會面
    with st.expander("👥 社會面 (GRI 400 系列) 指標目錄", expanded=True):
        gri_404_active = st.checkbox("GRI 404: 培訓與教育 (Training)", value=True, help="統計平均培訓時數與留才機制")
        selected_sub_404 = []
        if gri_404_active:
            selected_indicators.append("GRI 404")
            c1, c2 = st.columns([0.08, 0.92])
            with c2:
                if st.checkbox("├─ 4.1.1 員工平均培訓時數結構分析", value=True):
                    selected_sub_404.append("4.1.1")
                if st.checkbox("├─ 4.1.2 員工技能提升與成長規畫效益", value=True):
                    selected_sub_404.append("4.1.2")
                if st.checkbox("└─ 4.1.3 組織人才穩定度與流動率解讀", value=True):
                    selected_sub_404.append("4.1.3")
                    
        if st.checkbox("GRI 401: 員工聘用與流動 (Employment) [擴充功能]", value=False, help="統計新進員工與流動率指標"):
            selected_indicators.append("GRI 401")
        if st.checkbox("GRI 405: 多元與平等機會 (Diversity) [擴充功能]", value=False, help="統計主管與基層性別及年齡結構占比"):
            selected_indicators.append("GRI 405")
            
    # 分類三：治理與經濟面
    with st.expander("💼 治理與經濟面 (GRI 200 & 2 系列) 指標目錄", expanded=True):
        if st.checkbox("GRI 201: 經濟績效 (Economic Performance) [擴充功能]", value=False, help="統計組織直接產出與分配的經濟價值"):
            selected_indicators.append("GRI 201")
        if st.checkbox("GRI 205: 反貪腐 (Anti-corruption) [擴充功能]", value=False, help="誠信經營守則宣導與貪腐風險評估"):
            selected_indicators.append("GRI 205")
        if st.checkbox("GRI 2: 一般揭露 (General Disclosures) [擴充功能]", value=False, help="組織概況、報告實務與治理架構說明"):
            selected_indicators.append("GRI 2")
    
    target_words = st.slider("每項細部子章節 AI 寫作字數", min_value=150, max_value=600, value=350, step=50, help="決定地端 AI 撰寫各子細項（例如 3.1.1 範疇一分析）時的描述長度。字數越多，報告書內容越充實。")
    
    st.info(
        "💡 **安全合規說明**：本系統所有 AI 文本擴寫與計算，均在您的地端設備 (Localhost Ollama) 完成。 "
        "沒有任何商業機密數據會上傳至第三方公有雲端，符合最嚴格的企業資訊安全稽核要求。"
    )
    
    st.write("---")
    
    # 生成按鈕
    generate_btn = st.button("🚀 開始地端安全生成完整報告書", use_container_width=True, type="primary")

# ----------------- 生成邏輯觸發 -----------------
if generate_btn:
    # 基礎輸入檢核
    if not selected_indicators:
        st.warning("⚠️ 請至少選擇一個 GRI 揭露指標！")
        st.stop()
        
    has_305 = "GRI 305" in selected_indicators
    has_404 = "GRI 404" in selected_indicators
    
    # 提醒勾選擴充功能
    expanding_selected = [ind for ind in selected_indicators if ind not in ["GRI 305", "GRI 404"]]
    if expanding_selected:
        st.toast(f"💡 偵測到您勾選了擴充中指標 ({', '.join(expanding_selected)})，本版本將優先為您生成數據齊備的 GRI 305 與 GRI 404 報告書章節！", icon="ℹ️")
    
    if has_305 and not env_file:
        st.error("❌ 您選擇了 GRI 305 排放指標，但尚未上傳環境數據 Excel 檔案。")
        st.stop()
        
    if has_305 and not selected_sub_305:
        st.error("❌ 您啟用了 GRI 305 指標，但未勾選任何細部子項目。請勾選至少一個子項目！")
        st.stop()
        
    if has_404 and not soc_file:
        st.error("❌ 您選擇了 GRI 404 培訓與教育指標，但尚未上傳人資數據 Excel 檔案。")
        st.stop()
        
    if has_404 and not selected_sub_404:
        st.error("❌ 您啟用了 GRI 404 指標，但未勾選任何細部子項目。請勾選至少一個子項目！")
        st.stop()
        
    # 初始化處理進度與載入狀態
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    chapters_data = {}
    
    # 初始化 AI 經理與解析器
    ai_manager = ESGLLMManager(model_name=model_name, host=ollama_host)
    processor = ESGDataProcessor()
    
    try:
        # ------------ 步驟一：數據解析 ------------
        status_text.write("⏳ [1/3] 正在解析與清洗各部門上傳的 Excel 數據...")
        progress_bar.progress(20)
        time.sleep(0.5)
        
        if has_305:
            env_data = processor.process_environmental_excel(
                env_file.getvalue(), 
                company_name=company_name, 
                reporting_year=reporting_year,
                baseline_emissions=baseline_input
            )
            chapters_data["GRI 305"] = env_data
            
        if has_404:
            soc_data = processor.process_social_excel(
                soc_file.getvalue(), 
                company_name=company_name, 
                reporting_year=reporting_year
            )
            chapters_data["GRI 404"] = soc_data
            
        # ------------ 步驟二：AI 生成文本 ------------
        status_text.write("⏳ [2/3] 正在調度地端 Ollama AI 進行各細項子章節獨立寫作 (預計耗時 20~60 秒)...")
        progress_bar.progress(50)
        
        # 逐章細分段落生成
        if "GRI 305" in chapters_data:
            st.write("📝 正在撰寫：GRI 305 溫室氣體排放篇 (依勾選子項目生成)...")
            sub_chapters_305 = ai_manager.generate_chapter_subsections(
                chapters_data["GRI 305"], 
                "GRI 305", 
                target_words=target_words,
                selected_subs=selected_sub_305
            )
            chapters_data["GRI 305"]["sub_chapters"] = sub_chapters_305
            chapters_data["GRI 305"]["ai_text"] = "\n\n".join(sub_chapters_305.values())
            
        if "GRI 404" in chapters_data:
            st.write("📝 正在撰寫：GRI 404 培訓與教育篇 (依勾選子項目生成)...")
            sub_chapters_404 = ai_manager.generate_chapter_subsections(
                chapters_data["GRI 404"], 
                "GRI 404", 
                target_words=target_words,
                selected_subs=selected_sub_404
            )
            chapters_data["GRI 404"]["sub_chapters"] = sub_chapters_404
            chapters_data["GRI 404"]["ai_text"] = "\n\n".join(sub_chapters_404.values())
            
        # ------------ 步驟三：圖表繪製與 Word 封裝 ------------
        status_text.write("⏳ [3/3] 正在繪製統計圖表並進行 Word 文件組裝...")
        progress_bar.progress(80)
        time.sleep(0.5)
        
        builder = ESGReportBuilder()
        output_filepath = builder.build_full_report(company_name, reporting_year, chapters_data)
        
        progress_bar.progress(100)
        status_text.success("🎉 永續報告書初稿生成成功！")
        
        # 成果展示與下載
        st.balloons()
        st.write("---")
        st.markdown("### 📂 報告書生成成果與下載")
        
        # 讀取生成好的 Word 檔案以便使用者下載
        with open(output_filepath, "rb") as f:
            docx_bytes = f.read()
            
        filename = os.path.basename(output_filepath)
        
        # 顯示下載按鈕
        st.download_button(
            label="💾 一鍵下載完整 Word 報告書 (.docx)",
            data=docx_bytes,
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True
        )
        
        # 預覽區
        st.markdown("### 🔍 AI 生成文本即時預覽")
        if "GRI 305" in chapters_data:
            with st.expander("👁️ 預覽 GRI 305 溫室氣體排放量 3 大細部子項描述"):
                for sub_id, text in chapters_data["GRI 305"].get("sub_chapters", {}).items():
                    st.markdown(f"**子章節 {sub_id}**")
                    st.info(text)
                
        if "GRI 404" in chapters_data:
            with st.expander("👁️ 預覽 GRI 404 培訓與教育 3 大細部子項描述"):
                for sub_id, text in chapters_data["GRI 404"].get("sub_chapters", {}).items():
                    st.markdown(f"**子章節 {sub_id}**")
                    st.info(text)
                
    except Exception as e:
        status_text.empty()
        progress_bar.empty()
        st.error(f"❌ 報告書生成失敗！錯誤原因：{str(e)}")
