import streamlit as st
import os
import sys

# 確保路徑正確
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from test_esg_generation import generate_full_31_topics_mock
from modules.report_builder import ESGReportBuilder

# 設定網頁標題與排版
st.set_page_config(page_title="ESG 永續報告書管理系統", page_icon="🌱", layout="wide")

# 初始化機制 (Session State)
if "esg_data" not in st.session_state:
    # 預設企業名稱與年度
    default_company = "星光電子製造廠"
    default_year = "2025"
    
    # 載入全套 31 個重大主題的永續數據字典
    esg_data = generate_full_31_topics_mock(default_company, default_year)
    
    # 確保 GRI 305 排放數據結構完整並寫入預設值
    if "GRI 305" not in esg_data:
        esg_data["GRI 305"] = {}
    esg_data["GRI 305"]["emissions_data"] = {
        "scope_1_direct": {
            "柴油發電機": 150.5,
            "冷媒逸散": 45.2,
            "總計": 195.7
        },
        "scope_2_indirect": {
            "外購電力": 3250.8,
            "總計": 3250.8
        },
        "total_emissions_tCO2e": 3446.5,
        "yoy_change_percentage": -3.5
    }
    
    # 確保 GRI 302 能源消耗結構與預設值
    if "GRI 302" not in esg_data:
        esg_data["GRI 302"] = {}
    esg_data["GRI 302"]["energy_data"] = {
        "公務車汽油消耗量_公升": 4200.0
    }
    
    # 確保 GRI 306 廢棄物處理結構與預設值
    if "GRI 306" not in esg_data:
        esg_data["GRI 306"] = {}
    esg_data["GRI 306"]["waste_data"] = {
        "製程廢鋁鐵回收量_公斤": 8500.0
    }
    
    # 確保 GRI 404 培訓數據結構完整並寫入預設值
    if "GRI 404" not in esg_data:
        esg_data["GRI 404"] = {}
    esg_data["GRI 404"]["social_data"] = {
        "training_metrics": {
            "中高階主管平均培訓時數": {"value": 35.0, "unit": "小時"},
            "基層員工平均培訓時數": {"value": 28.0, "unit": "小時"},
            "全體員工平均培訓時數": {"value": 31.5, "unit": "小時"}
        }
    }
    
    # 確保 GRI 401 結構完整並寫入預設值
    if "GRI 401" not in esg_data:
        esg_data["GRI 401"] = {}
    esg_data["GRI 401"]["employment_data"] = {
        "turnover_metrics": {
            "年度新進員工人數_人": 25,
            "年度離職員工人數_人": 20,
            "員工總數_人": 240,
            "新進員工比率": {"value": 10.4, "unit": "%"},
            "員工離職率": {"value": 8.3, "unit": "%"}
        }
    }
    
    # 確保 GRI 201 結構完整並寫入預設值
    if "GRI 201" not in esg_data:
        esg_data["GRI 201"] = {}
    esg_data["GRI 201"]["economic_data"] = {
        "年度總營業收入_萬元": 52000.0
    }
    
    # 確保 GRI 205 結構完整並寫入預設值
    if "GRI 205" not in esg_data:
        esg_data["GRI 205"] = {}
    esg_data["GRI 205"]["anti_corruption_data"] = {
        "董事會成員完成反貪腐培訓人數_人": 7,
        "確定的貪腐與收賄違規事件_件": 0
    }
    
    # 確保 GRI 2 一般揭露結構與預設值
    if "GRI 2" not in esg_data:
        esg_data["GRI 2"] = {}
    esg_data["GRI 2"]["general_data"] = {
        "員工總數_人": 240
    }
        
    st.session_state["esg_data"] = esg_data
    st.session_state["company_name"] = default_company
    st.session_state["reporting_year"] = default_year

# 網頁左側：動態數據修改面板 (st.sidebar)
st.sidebar.markdown("# ⚙️ 永續數據動態修改")
st.sidebar.write("請在此調整核心指標數據，右側儀表板與報告書將即時更新。")

# 1. 頂部基本宣告
company_name = st.sidebar.text_input("企業名稱", value=st.session_state["company_name"])
reporting_year = st.sidebar.text_input("報告年度", value=st.session_state["reporting_year"])

# 更新 session_state 中的名稱與年度
st.session_state["company_name"] = company_name
st.session_state["reporting_year"] = reporting_year

# 2. 🌱 【E 環境面管理】互動欄位
with st.sidebar.expander("🌱 【E 環境面管理】互動欄位", expanded=True):
    diesel_val = st.number_input(
        "GRI 305：柴油發電機碳排 (公噸 CO2e)",
        min_value=0.0,
        max_value=10000.0,
        value=float(st.session_state["esg_data"]["GRI 305"]["emissions_data"]["scope_1_direct"]["柴油發電機"]),
        step=1.0,
        key="sb_diesel"
    )
    electricity_val = st.number_input(
        "GRI 305：外購電力碳排 (公噸 CO2e)",
        min_value=0.0,
        max_value=100000.0,
        value=float(st.session_state["esg_data"]["GRI 305"]["emissions_data"]["scope_2_indirect"]["外購電力"]),
        step=10.0,
        key="sb_electricity"
    )
    gasoline_val = st.number_input(
        "GRI 302：公務車汽油消耗量 (公升)",
        min_value=0.0,
        max_value=100000.0,
        value=float(st.session_state["esg_data"]["GRI 302"]["energy_data"]["公務車汽油消耗量_公升"]),
        step=10.0,
        key="sb_gasoline"
    )
    waste_recycle_val = st.number_input(
        "GRI 306：製程廢鋁鐵回收量 (公斤)",
        min_value=0.0,
        max_value=1000000.0,
        value=float(st.session_state["esg_data"]["GRI 306"]["waste_data"]["製程廢鋁鐵回收量_公斤"]),
        step=50.0,
        key="sb_waste"
    )

# 3. 👥 【S 社會面關係】互動欄位
with st.sidebar.expander("👥 【S 社會面關係】互動欄位", expanded=True):
    base_training_hours = st.slider(
        "GRI 404：基層員工平均培訓時數 (小時)",
        min_value=0.0,
        max_value=120.0,
        value=float(st.session_state["esg_data"]["GRI 404"]["social_data"]["training_metrics"]["基層員工平均培訓時數"]["value"]),
        step=0.5,
        key="sb_base_training"
    )
    manager_training_hours = st.slider(
        "GRI 404：中高階主管平均培訓時數 (小時)",
        min_value=0.0,
        max_value=120.0,
        value=float(st.session_state["esg_data"]["GRI 404"]["social_data"]["training_metrics"]["中高階主管平均培訓時數"]["value"]),
        step=0.5,
        key="sb_manager_training"
    )
    new_hires = st.number_input(
        "GRI 401：年度新進員工人數 (人)",
        min_value=0,
        max_value=1000,
        value=int(st.session_state["esg_data"]["GRI 401"]["employment_data"]["turnover_metrics"]["年度新進員工人數_人"]),
        step=1,
        key="sb_new_hires"
    )
    terminations = st.number_input(
        "GRI 401：年度離職員工人數 (人)",
        min_value=0,
        max_value=1000,
        value=int(st.session_state["esg_data"]["GRI 401"]["employment_data"]["turnover_metrics"]["年度離職員工人數_人"]),
        step=1,
        key="sb_terminations"
    )

# 4. ⚖️ 【G 公司治理面】互動欄位
with st.sidebar.expander("⚖️ 【G 公司治理面】互動欄位", expanded=True):
    revenue = st.number_input(
        "GRI 201：年度總營業收入 (萬元)",
        min_value=0.0,
        max_value=10000000.0,
        value=float(st.session_state["esg_data"]["GRI 201"]["economic_data"]["年度總營業收入_萬元"]),
        step=100.0,
        key="sb_revenue"
    )
    anti_corruption_training = st.number_input(
        "GRI 205：董事會成員完成反貪腐培訓人數 (人)",
        min_value=0,
        max_value=100,
        value=int(st.session_state["esg_data"]["GRI 205"]["anti_corruption_data"]["董事會成員完成反貪腐培訓人數_人"]),
        step=1,
        key="sb_anti_corruption"
    )
    corruption_cases = st.number_input(
        "GRI 205：確定的貪腐與收賄違規事件 (件)",
        min_value=0,
        max_value=100,
        value=int(st.session_state["esg_data"]["GRI 205"]["anti_corruption_data"]["確定的貪腐與收賄違規事件_件"]),
        step=1,
        key="sb_corruption_cases"
    )

# 同步更新回 st.session_state 數據字典
# 更新 GRI 305
st.session_state["esg_data"]["GRI 305"]["emissions_data"]["scope_1_direct"]["柴油發電機"] = diesel_val
refrigerant_emissions = st.session_state["esg_data"]["GRI 305"]["emissions_data"]["scope_1_direct"].get("冷媒逸散", 45.2)
scope_1_total = round(diesel_val + refrigerant_emissions, 2)
st.session_state["esg_data"]["GRI 305"]["emissions_data"]["scope_1_direct"]["總計"] = scope_1_total

st.session_state["esg_data"]["GRI 305"]["emissions_data"]["scope_2_indirect"]["外購電力"] = electricity_val
st.session_state["esg_data"]["GRI 305"]["emissions_data"]["scope_2_indirect"]["總計"] = electricity_val

total_emissions = round(scope_1_total + electricity_val, 2)
st.session_state["esg_data"]["GRI 305"]["emissions_data"]["total_emissions_tCO2e"] = total_emissions

# 計算 YoY (基準年設為 3571.5)
baseline = 3571.5
yoy_change = round(((total_emissions - baseline) / baseline) * 100, 2)
st.session_state["esg_data"]["GRI 305"]["emissions_data"]["yoy_change_percentage"] = yoy_change

# 更新 GRI 302
st.session_state["esg_data"]["GRI 302"]["energy_data"]["公務車汽油消耗量_公升"] = gasoline_val

# 更新 GRI 306
st.session_state["esg_data"]["GRI 306"]["waste_data"]["製程廢鋁鐵回收量_公斤"] = waste_recycle_val

# 更新 GRI 404
st.session_state["esg_data"]["GRI 404"]["social_data"]["training_metrics"]["基層員工平均培訓時數"]["value"] = base_training_hours
st.session_state["esg_data"]["GRI 404"]["social_data"]["training_metrics"]["中高階主管平均培訓時數"]["value"] = manager_training_hours
overall_hours = round((base_training_hours + manager_training_hours) / 2, 2)
st.session_state["esg_data"]["GRI 404"]["social_data"]["training_metrics"]["全體員工平均培訓時數"]["value"] = overall_hours

# 更新 GRI 401 & 員工流動率
employee_total = st.session_state["esg_data"]["GRI 2"]["general_data"]["員工總數_人"]
st.session_state["esg_data"]["GRI 401"]["employment_data"]["turnover_metrics"]["年度新進員工人數_人"] = new_hires
st.session_state["esg_data"]["GRI 401"]["employment_data"]["turnover_metrics"]["年度離職員工人數_人"] = terminations
new_hire_rate = round((new_hires / employee_total) * 100, 2)
turnover_rate = round((terminations / employee_total) * 100, 2)
st.session_state["esg_data"]["GRI 401"]["employment_data"]["turnover_metrics"]["新進員工比率"]["value"] = new_hire_rate
st.session_state["esg_data"]["GRI 401"]["employment_data"]["turnover_metrics"]["員工離職率"]["value"] = turnover_rate

# 更新 GRI 201
st.session_state["esg_data"]["GRI 201"]["economic_data"]["年度總營業收入_萬元"] = revenue

# 更新 GRI 205
st.session_state["esg_data"]["GRI 205"]["anti_corruption_data"]["董事會成員完成反貪腐培訓人數_人"] = anti_corruption_training
st.session_state["esg_data"]["GRI 205"]["anti_corruption_data"]["確定的貪腐與收賄違規事件_件"] = corruption_cases

# 同步更新所有章節的公司名稱與年度
for key in st.session_state["esg_data"]:
    st.session_state["esg_data"][key]["company_name"] = company_name
    st.session_state["esg_data"][key]["reporting_year"] = reporting_year


# 網頁右側：動態展示與一鍵下載 (st.main)
# Custom CSS for UI
st.markdown("""
<style>
    .metric-card {
        background-color: #f8f9fa;
        padding: 1.2rem;
        border-radius: 10px;
        border: 1px solid #dee2e6;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        text-align: center;
        min-height: 110px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .metric-value {
        font-size: 1.6rem;
        font-weight: bold;
        color: #2E7D32;
        word-break: break-all;
    }
    .metric-label {
        font-size: 0.95rem;
        color: #6c757d;
        margin-top: 0.3rem;
    }
</style>
""", unsafe_allow_html=True)

st.title("🌱 永續報告書數據互動與展示系統")
st.markdown(f"### 當前企業：{company_name} | 報告年度：{reporting_year} 年度")

# 1. Dashboard 摘要展示
st.markdown("#### 📊 當前核心數據摘要 (Dashboard)")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{company_name} ({reporting_year})</div>
        <div class="metric-label">企業與申報年度</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{total_emissions} tCO2e</div>
        <div class="metric-label">總碳排放量 (Scope 1+2)</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{overall_hours} 小時</div>
        <div class="metric-label">全體員工平均培訓時數</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{turnover_rate} %</div>
        <div class="metric-label">員工流動率 (離職率)</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# 2. 一鍵重新編譯與下載
st.markdown("#### 🚀 報告書排版引擎")
st.write("點擊下方按鈕以最新修改的數據重新編譯完整 78 頁 Word 永續報告書草案：")

if st.button("🚀 一鍵重新編譯 78 頁正式報告書", use_container_width=True):
    with st.spinner("正在啟動後端排版引擎，執行全指標多斷頁組裝..."):
        try:
            builder = ESGReportBuilder()
            output_filepath = builder.build_full_report(company_name, reporting_year, st.session_state["esg_data"])
            st.session_state["compiled_filepath"] = output_filepath
            st.session_state["compiled_ready"] = True
            st.success("🎉 78 頁永續報告書草案重新編譯成功！")
        except Exception as e:
            st.error(f"❌ 編譯報告書失敗: {e}")

# 顯示下載按鈕
if st.session_state.get("compiled_ready"):
    filepath = st.session_state["compiled_filepath"]
    if os.path.exists(filepath):
        with open(filepath, "rb") as file_bytes:
            st.download_button(
                label="📥 下載產出之 Word 正式草案 (.docx)",
                data=file_bytes,
                file_name=os.path.basename(filepath),
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True
            )
