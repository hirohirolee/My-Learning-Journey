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

def generate_energy_template():
    """產出 GRI 302 能源消耗 Excel 二進位資料"""
    df = pd.DataFrame([
        {"能源種類": "外購電力", "消耗量": 5620000.0, "單位": "度"},
        {"能源種類": "柴油", "消耗量": 12500.0, "單位": "公升"},
        {"能源種類": "汽油", "消耗量": 4200.0, "單位": "公升"},
        {"能源種類": "總能源消耗", "消耗量": 20628.0, "單位": "GJ"},
        {"能源種類": "能源密集度", "消耗量": 4.2, "單位": "GJ_百萬營收"}
    ])
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name="Energy Data")
    return output.getvalue()

def generate_waste_template():
    """產出 GRI 306 廢棄物與回收 Excel 二進位資料"""
    df = pd.DataFrame([
        {"指標名稱": "有害事業廢棄物_噸", "數值": 1.2},
        {"指標名稱": "一般事業廢棄物_噸", "數值": 45.8},
        {"指標名稱": "廢棄物回收率_百分比", "數值": 85.3},
        {"指標名稱": "處理方式_委外焚化_噸", "數值": 8.5},
        {"指標名稱": "處理方式_衛生掩埋_噸", "數值": 5.7}
    ])
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name="Waste Data")
    return output.getvalue()

def generate_employment_template():
    """產出 GRI 401 員工流動 Excel 二進位資料"""
    df = pd.DataFrame([
        {"指標名稱": "新進員工總數_人", "數值": 25},
        {"指標名稱": "新進率_百分比", "數值": 10.4},
        {"指標名稱": "離職員工總數_人", "數值": 20},
        {"指標名稱": "離職率_百分比", "數值": 8.3}
    ])
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name="Employment Data")
    return output.getvalue()

def generate_diversity_template():
    """產出 GRI 405 多元機會 Excel 二進位資料"""
    df = pd.DataFrame([
        {"指標名稱": "管理階層男性佔比_百分比", "數值": 60.0},
        {"指標名稱": "管理階層女性佔比_百分比", "數值": 40.0},
        {"指標名稱": "基層員工男性佔比_百分比", "數值": 55.0},
        {"指標名稱": "基層員工女性佔比_百分比", "數值": 45.0},
        {"指標名稱": "員工年齡結構_30歲以下_百分比", "數值": 15.0},
        {"指標名稱": "員工年齡結構_30至50歲_百分比", "數值": 65.0},
        {"指標名稱": "員工年齡結構_50歲以上_百分比", "數值": 20.0}
    ])
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name="Diversity Data")
    return output.getvalue()

def generate_economic_template():
    """產出 GRI 201 經濟績效 Excel 二進位資料"""
    df = pd.DataFrame([
        {"項目名稱": "營業收入_萬元", "金額_萬元": 52000.0},
        {"項目名稱": "營運成本_萬元", "金額_萬元": 38000.0},
        {"項目名稱": "員工薪資與福利_萬元", "金額_萬元": 8500.0},
        {"項目名稱": "支付給出資人股息_萬元", "金額_萬元": 1200.0},
        {"項目名稱": "支付給公部門稅收_萬元", "金額_萬元": 300.0},
        {"項目名稱": "社區投資_萬元", "金額_萬元": 30.0},
        {"項目名稱": "保留經濟價值_萬元", "金額_萬元": 3970.0}
    ])
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name="Economic Data")
    return output.getvalue()

def generate_anti_corruption_template():
    """產出 GRI 205 反貪腐 Excel 二進位資料"""
    df = pd.DataFrame([
        {"指標名稱": "董事反貪腐守則簽署率_百分比", "數值": 100.0},
        {"指標名稱": "員工反貪腐宣導完成率_百分比", "數值": 100.0},
        {"指標名稱": "人均反貪腐培訓時數_小時", "數值": 2.0},
        {"指標名稱": "貪腐確立案件_件", "數值": 0}
    ])
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name="Anti-Corruption Data")
    return output.getvalue()

def generate_general_template():
    """產出 GRI 2 一般揭露 Excel 二進位資料"""
    df = pd.DataFrame([
        {"指標名稱": "員工總數_人", "數值": 240},
        {"指標名稱": "營運據點_說明", "數值": "台灣台北總部、桃園生產工廠"},
        {"指標名稱": "主要產品_說明", "數值": "電子零組件與製造服務"},
        {"指標名稱": "公司實收資本額_億元", "數值": 2.0}
    ])
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name="General Data")
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
    st.markdown('<div class="card"><h3>📥 數據上傳與模板下載</h3></div>', unsafe_allow_html=True)
    st.write("您可以下載標準範本，或直接上傳您企業的數據表格。未上傳者將啟用預設模擬數據。")
    
    upload_tab1, upload_tab2, upload_tab3, upload_tab4 = st.tabs(["🍀 GRI 305 & 404", "⚡ GRI 302 & 306", "👥 GRI 401 & 405", "💼 經濟與治理"])
    
    with upload_tab1:
        st.write("**GRI 305 溫室氣體與 GRI 404 培訓教育**")
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
        env_file = st.file_uploader("上傳 GRI 305 環境數據 Excel", type=["xlsx"], key="env_upload")
        soc_file = st.file_uploader("上傳 GRI 404 人資數據 Excel", type=["xlsx"], key="soc_upload")
        
    with upload_tab2:
        st.write("**GRI 302 能源消耗與 GRI 306 廢棄物回收**")
        t2_col1, t2_col2 = st.columns(2)
        with t2_col1:
            st.download_button(
                label="📊 下載能源數據模板 (.xlsx)",
                data=generate_energy_template(),
                file_name="GRI_302_能源數據模板.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        with t2_col2:
            st.download_button(
                label="🗑️ 下載廢棄物數據模板 (.xlsx)",
                data=generate_waste_template(),
                file_name="GRI_306_廢棄物數據模板.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        st.write("")
        energy_file = st.file_uploader("上傳 GRI 302 能源數據 Excel (能源種類、消耗量、單位)", type=["xlsx"], key="energy_upload")
        waste_file = st.file_uploader("上傳 GRI 306 廢棄物數據 Excel (指標名稱、數值)", type=["xlsx"], key="waste_upload")
        
    with upload_tab3:
        st.write("**GRI 401 員工流動與 GRI 405 多元機會**")
        t3_col1, t3_col2 = st.columns(2)
        with t3_col1:
            st.download_button(
                label="👥 下載員工流動模板 (.xlsx)",
                data=generate_employment_template(),
                file_name="GRI_401_員工流動模板.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        with t3_col2:
            st.download_button(
                label="🌈 下載多元機會模板 (.xlsx)",
                data=generate_diversity_template(),
                file_name="GRI_405_多元機會模板.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        st.write("")
        employment_file = st.file_uploader("上傳 GRI 401 員工流動 Excel (指標名稱、數值)", type=["xlsx"], key="employment_upload")
        diversity_file = st.file_uploader("上傳 GRI 405 多元平等 Excel (指標名稱、數值)", type=["xlsx"], key="diversity_upload")
        
    with upload_tab4:
        st.write("**GRI 201 經濟績效、GRI 205 反貪腐與 GRI 2 一般揭露**")
        t4_col1, t4_col2, t4_col3 = st.columns(3)
        with t4_col1:
            st.download_button(
                label="💰 經濟績效模板",
                data=generate_economic_template(),
                file_name="GRI_201_經濟績效模板.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        with t4_col2:
            st.download_button(
                label="⚖️ 反貪腐模板",
                data=generate_anti_corruption_template(),
                file_name="GRI_205_反貪腐模板.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        with t4_col3:
            st.download_button(
                label="🏢 一般揭露模板",
                data=generate_general_template(),
                file_name="GRI_2_一般揭露模板.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        st.write("")
        economic_file = st.file_uploader("上傳 GRI 201 經濟績效 Excel (項目名稱、金額_萬元)", type=["xlsx"], key="economic_upload")
        anti_corruption_file = st.file_uploader("上傳 GRI 205 反貪腐 Excel (指標名稱、數值)", type=["xlsx"], key="anti_corruption_upload")
        general_file = st.file_uploader("上傳 GRI 2 一般揭露 Excel (項目、內容說明)", type=["xlsx"], key="general_upload")

with col2:
    st.markdown('<div class="card"><h3>📑 揭露指標設定</h3></div>', unsafe_allow_html=True)
    
    st.write("請勾選要導入報告書之 GRI 揭露指標與細部子項目：")
    selected_indicators = []
    
    # 分類一：環境面
    with st.expander("🍀 環境面 (GRI 300 系列) 指標目錄", expanded=True):
        # GRI 305
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
                    
        # GRI 302
        gri_302_active = st.checkbox("GRI 302: 能源消耗 (Energy)", value=False, help="統計柴油、電力等能源耗用與能效分析")
        selected_sub_302 = []
        if gri_302_active:
            selected_indicators.append("GRI 302")
            c1, c2 = st.columns([0.08, 0.92])
            with c2:
                if st.checkbox("├─ 3.2.1 組織內部能源消耗數據解讀", value=True):
                    selected_sub_302.append("3.2.1")
                if st.checkbox("└─ 3.2.2 能源密集度與節能減量成效", value=True):
                    selected_sub_302.append("3.2.2")
                    
        # GRI 306
        gri_306_active = st.checkbox("GRI 306: 廢棄物與回收 (Waste)", value=False, help="統計廢棄物產生與流向管理")
        selected_sub_306 = []
        if gri_306_active:
            selected_indicators.append("GRI 306")
            c1, c2 = st.columns([0.08, 0.92])
            with c2:
                if st.checkbox("├─ 3.6.1 廢棄物產生源與源頭減量措施", value=True):
                    selected_sub_306.append("3.6.1")
                if st.checkbox("├─ 3.6.2 廢棄物回收與循環再利用效益", value=True):
                    selected_sub_306.append("3.6.2")
                if st.checkbox("└─ 3.6.3 廢棄物最終處置與合規評估", value=True):
                    selected_sub_306.append("3.6.3")
            
    # 分類二：社會面
    with st.expander("👥 社會面 (GRI 400 系列) 指標目錄", expanded=True):
        # GRI 404
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
                    
        # GRI 401
        gri_401_active = st.checkbox("GRI 401: 員工聘用與流動 (Employment)", value=False, help="統計新進員工與流動率指標")
        selected_sub_401 = []
        if gri_401_active:
            selected_indicators.append("GRI 401")
            c1, c2 = st.columns([0.08, 0.92])
            with c2:
                if st.checkbox("├─ 4.1.1.b 員工流動率與新進率結構解讀", value=True):
                    selected_sub_401.append("4.1.1.b")
                if st.checkbox("└─ 4.1.2 關懷福利政策與育嬰留停成效", value=True):
                    selected_sub_401.append("4.1.2")
                    
        # GRI 405
        gri_405_active = st.checkbox("GRI 405: 多元與平等機會 (Diversity)", value=False, help="統計主管與基層性別及年齡結構占比")
        selected_sub_405 = []
        if gri_405_active:
            selected_indicators.append("GRI 405")
            c1, c2 = st.columns([0.08, 0.92])
            with c2:
                if st.checkbox("├─ 4.5.1 治理機構與員工結構多元化比例", value=True):
                    selected_sub_405.append("4.5.1")
                if st.checkbox("└─ 4.5.2 男女同工同酬與平等晉升機會", value=True):
                    selected_sub_405.append("4.5.2")
            
    # 分類三：治理與經濟面
    with st.expander("💼 治理與經濟面 (GRI 200 & 2 系列) 指標目錄", expanded=True):
        # GRI 201
        gri_201_active = st.checkbox("GRI 201: 經濟績效 (Economic Performance)", value=False, help="統計組織直接產出與分配的經濟價值")
        selected_sub_201 = []
        if gri_201_active:
            selected_indicators.append("GRI 201")
            c1, c2 = st.columns([0.08, 0.92])
            with c2:
                if st.checkbox("├─ 2.1.1 直接產生與分配之經濟價值分析", value=True):
                    selected_sub_201.append("2.1.1")
                if st.checkbox("└─ 2.1.2 氣候變遷對企業營運之財務衝擊", value=True):
                    selected_sub_201.append("2.1.2")
                    
        # GRI 205
        gri_205_active = st.checkbox("GRI 205: 反貪腐 (Anti-corruption)", value=False, help="誠信經營守則宣導與貪腐風險評估")
        selected_sub_205 = []
        if gri_205_active:
            selected_indicators.append("GRI 205")
            c1, c2 = st.columns([0.08, 0.92])
            with c2:
                if st.checkbox("├─ 2.5.1 反貪腐政策傳達、簽署與培訓統計", value=True):
                    selected_sub_205.append("2.5.1")
                if st.checkbox("└─ 2.5.2 誠信經營確立事件與檢舉防範機制", value=True):
                    selected_sub_205.append("2.5.2")
                    
        # GRI 2
        gri_2_active = st.checkbox("GRI 2: 一般揭露 (General Disclosures)", value=False, help="組織概況、報告實務與治理架構說明")
        selected_sub_2 = []
        if gri_2_active:
            selected_indicators.append("GRI 2")
            c1, c2 = st.columns([0.08, 0.92])
            with c2:
                if st.checkbox("├─ 2.2.1 組織基本概況、據點與資本規模", value=True):
                    selected_sub_2.append("2.2.1")
                if st.checkbox("├─ 2.2.2 商業活動與供應鏈價值關係", value=True):
                    selected_sub_2.append("2.2.2")
                if st.checkbox("└─ 2.2.3 員工聘用特性與人力資源分佈", value=True):
                    selected_sub_2.append("2.2.3")
    
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
        
    # 驗證每個選定指標的子項目是否至少勾選一個
    for ind, active, sub_list, name in [
        ("GRI 305", gri_305_active, selected_sub_305, "GRI 305 溫室氣體排放"),
        ("GRI 302", gri_302_active, selected_sub_302, "GRI 302 能源消耗"),
        ("GRI 306", gri_306_active, selected_sub_306, "GRI 306 廢棄物與回收"),
        ("GRI 404", gri_404_active, selected_sub_404, "GRI 404 培訓與教育"),
        ("GRI 401", gri_401_active, selected_sub_401, "GRI 401 員工聘用與流動"),
        ("GRI 405", gri_405_active, selected_sub_405, "GRI 405 多元與平等機會"),
        ("GRI 201", gri_201_active, selected_sub_201, "GRI 201 經濟績效"),
        ("GRI 205", gri_205_active, selected_sub_205, "GRI 205 反貪腐"),
        ("GRI 2", gri_2_active, selected_sub_2, "GRI 2 一般揭露")
    ]:
        if active and not sub_list:
            st.error(f"❌ 您啟用了 {name} 指標，但未勾選任何細部子項目。請勾選至少一個子項目！")
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
        
        if "GRI 305" in selected_indicators:
            env_data = processor.process_environmental_excel(
                env_file.getvalue() if env_file else None, 
                company_name=company_name, 
                reporting_year=reporting_year,
                baseline_emissions=baseline_input
            )
            chapters_data["GRI 305"] = env_data
            
        if "GRI 404" in selected_indicators:
            soc_data = processor.process_social_excel(
                soc_file.getvalue() if soc_file else None, 
                company_name=company_name, 
                reporting_year=reporting_year
            )
            chapters_data["GRI 404"] = soc_data

        if "GRI 302" in selected_indicators:
            energy_data = processor.process_energy_excel(
                energy_file.getvalue() if energy_file else None, 
                company_name=company_name, 
                reporting_year=reporting_year
            )
            chapters_data["GRI 302"] = energy_data

        if "GRI 306" in selected_indicators:
            waste_data = processor.process_waste_excel(
                waste_file.getvalue() if waste_file else None, 
                company_name=company_name, 
                reporting_year=reporting_year
            )
            chapters_data["GRI 306"] = waste_data

        if "GRI 401" in selected_indicators:
            employment_data = processor.process_employment_excel(
                employment_file.getvalue() if employment_file else None, 
                company_name=company_name, 
                reporting_year=reporting_year
            )
            chapters_data["GRI 401"] = employment_data

        if "GRI 405" in selected_indicators:
            diversity_data = processor.process_diversity_excel(
                diversity_file.getvalue() if diversity_file else None, 
                company_name=company_name, 
                reporting_year=reporting_year
            )
            chapters_data["GRI 405"] = diversity_data

        if "GRI 201" in selected_indicators:
            economic_data = processor.process_economic_excel(
                economic_file.getvalue() if economic_file else None, 
                company_name=company_name, 
                reporting_year=reporting_year
            )
            chapters_data["GRI 201"] = economic_data

        if "GRI 205" in selected_indicators:
            anti_corruption_data = processor.process_anti_corruption_excel(
                anti_corruption_file.getvalue() if anti_corruption_file else None, 
                company_name=company_name, 
                reporting_year=reporting_year
            )
            chapters_data["GRI 205"] = anti_corruption_data

        if "GRI 2" in selected_indicators:
            general_data = processor.process_general_disclosure_excel(
                general_file.getvalue() if general_file else None, 
                company_name=company_name, 
                reporting_year=reporting_year
            )
            chapters_data["GRI 2"] = general_data
            
        # ------------ 步驟二：AI 生成文本 ------------
        status_text.write("⏳ [2/3] 正在調度地端 Ollama AI 進行各細項子章節獨立寫作 (預計耗時 20~60 秒)...")
        progress_bar.progress(50)
        
        # 逐章細分段落生成
        for ch_code in selected_indicators:
            st.write(f"📝 正在撰寫：{ch_code} (依勾選項目生成)...")
            
            selected_subs = None
            if ch_code == "GRI 305":
                selected_subs = selected_sub_305
            elif ch_code == "GRI 404":
                selected_subs = selected_sub_404
            elif ch_code == "GRI 302":
                selected_subs = selected_sub_302
            elif ch_code == "GRI 306":
                selected_subs = selected_sub_306
            elif ch_code == "GRI 401":
                selected_subs = selected_sub_401
            elif ch_code == "GRI 405":
                selected_subs = selected_sub_405
            elif ch_code == "GRI 201":
                selected_subs = selected_sub_201
            elif ch_code == "GRI 205":
                selected_subs = selected_sub_205
            elif ch_code == "GRI 2":
                selected_subs = selected_sub_2
                
            sub_chapters = ai_manager.generate_chapter_subsections(
                chapters_data[ch_code], 
                ch_code, 
                target_words=target_words,
                selected_subs=selected_subs
            )
            chapters_data[ch_code]["sub_chapters"] = sub_chapters
            chapters_data[ch_code]["ai_text"] = "\n\n".join(sub_chapters.values())
            
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
        
        with open(output_filepath, "rb") as f:
            docx_bytes = f.read()
            
        filename = os.path.basename(output_filepath)
        
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
                
    except Exception as e:
        status_text.empty()
        progress_bar.empty()
        st.error(f"❌ 報告書生成失敗！錯誤原因：{str(e)}")
