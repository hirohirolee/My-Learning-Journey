"""
app.py — 企業數位韌性 AI 導航系統（Streamlit 前端）
功能：即時數據監控 Dashboard + 手動/自動稽核觸發 + CAPA 報告閱覽
"""

import time
import json
import requests
import pandas as pd
import streamlit as st
import threading
from datetime import datetime
import os
import sys
import socket
import subprocess
from dotenv import load_dotenv

# ── 環境變數與自動啟動後端 ──────────────────────────────────
# 載入專案根目錄的 .env 檔案 (本地測試與 Streamlit 運作設定)
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_CURRENT_DIR)
_DOTENV_PATH = os.path.join(_PROJECT_ROOT, ".env")
if os.path.exists(_DOTENV_PATH):
    load_dotenv(_DOTENV_PATH)
else:
    load_dotenv()

def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1.0)
        return s.connect_ex(('127.0.0.1', port)) == 0

def ensure_backend_running():
    port = 8000
    if is_port_in_use(port):
        return True
    
    try:
        backend_main = os.path.join(_PROJECT_ROOT, "backend", "main.py")
        if not os.path.exists(backend_main):
            st.warning(f"⚠️ 找不到後端主程式：{backend_main}")
            return False
        
        # 設定環境變數 PYTHONPATH，讓 uvicorn 能夠正確 import backend.main
        env = os.environ.copy()
        if "PYTHONPATH" in env:
            env["PYTHONPATH"] = f"{_PROJECT_ROOT}{os.pathsep}{env['PYTHONPATH']}"
        else:
            env["PYTHONPATH"] = _PROJECT_ROOT
            
        # 啟動後端子程序 (並記錄日誌以利排錯，放在 .venv 底下防止 Streamlit 檔案監聽器觸發重複重載)
        log_path = os.path.join(_PROJECT_ROOT, ".venv", "backend.log")
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        log_file = open(log_path, "a", encoding="utf-8")
        log_file.write(f"\n--- Starting backend at {datetime.now()} ---\n")
        log_file.write(f"sys.executable: {sys.executable}\n")
        log_file.write(f"PYTHONPATH: {env.get('PYTHONPATH')}\n")
        log_file.flush()
        
        subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", str(port)],
            cwd=_PROJECT_ROOT,
            env=env,
            stdout=log_file,
            stderr=log_file
        )
        
        # 等待後端啟動完成 (最多等待 10 秒)
        for _ in range(10):
            time.sleep(1)
            if is_port_in_use(port):
                return True
        return False
    except Exception as e:
        st.error(f"❌ 無法啟動後端子程序：{e}")
        return False

# 確保後端服務啟動中
ensure_backend_running()

# ── 初始化 Session State 與 Callbacks ─────────────────────────
if "token" not in st.session_state:
    st.session_state["token"] = None
if "role" not in st.session_state:
    st.session_state["role"] = None

# 阻斷式登入表單
if not st.session_state["token"]:
    st.markdown("""
    <div style="text-align: center; padding: 2rem;">
        <h1 style="color: #1e40af; font-family: 'Outfit', sans-serif;">🛡️ 私有化 AI 稽核決策中心</h1>
        <p style="color: #94a3b8; font-size: 1.1rem;">ISO 14064-1 ｜ ISO 27001 ｜ ISO 9001 決策中樞</p>
    </div>
    """, unsafe_allow_html=True)
    
    col_log1, col_log2, col_log3 = st.columns([1, 2, 1])
    with col_log2:
        with st.container(border=True):
            st.subheader("🔑 帳號身分驗證")
            username = st.text_input("帳號 (Username)", placeholder="例如: admin, qms, ciso")
            password = st.text_input("密碼 (Password)", type="password", placeholder="請輸入密碼")
            submit = st.button("🚀 登入系統", use_container_width=True, type="primary")
            
            if submit:
                if not username or not password:
                    st.error("⚠️ 請輸入帳號與密碼")
                else:
                    try:
                        backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")
                        r = requests.post(f"{backend_url}/api/login", json={"username": username, "password": password}, timeout=5)
                        if r.status_code == 200:
                            data = r.json()
                            st.session_state["token"] = data.get("token")
                            st.session_state["role"] = data.get("role")
                            st.success("🎉 登入成功！正在載入戰情系統...")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("❌ 登入失敗：帳號或密碼錯誤")
                    except Exception as e:
                        st.error(f"❌ 連線後端伺服器失敗：{e}")
            
            st.divider()
            st.markdown("""
            <div style="font-size: 0.85rem; color: #64748b; line-height: 1.5;">
                <strong>💡 測試帳號提示：</strong><br>
                • 系統管理員：<code>admin</code> / <code>admin123</code> (角色: <code>admin</code>)<br>
                • 生管經理：<code>qms</code> / <code>qms123</code> (角色: <code>qms_manager</code>)<br>
                • 資安長：<code>ciso</code> / <code>ciso123</code> (角色: <code>ciso</code>)
            </div>
            """, unsafe_allow_html=True)
    st.stop()

if "sim_carbon" not in st.session_state: st.session_state["sim_carbon"] = 1.45
if "sim_yield" not in st.session_state: st.session_state["sim_yield"] = 79.3
if "sim_user" not in st.session_state: st.session_state["sim_user"] = "EMP-2847"
if "sim_dept" not in st.session_state: st.session_state["sim_dept"] = "製造一部"
if "sim_shift" not in st.session_state: st.session_state["sim_shift"] = "A班"
if "sim_equip" not in st.session_state: st.session_state["sim_equip"] = "SMT-LINE-03"
if "sim_log" not in st.session_state: st.session_state["sim_log"] = (
    "2025-01-15 03:42 midnight high-volume download: user downloaded 67 compliance "
    "asset files from IP 192.168.1.105. Download count exceeded threshold."
)

# [DEMO FEATURE] 初始化情境展示 State
if "demo_task_id" not in st.session_state:
    st.session_state["demo_task_id"] = None
if "demo_status" not in st.session_state:
    st.session_state["demo_status"] = "idle"
if "demo_report" not in st.session_state:
    st.session_state["demo_report"] = None

# [Agentic HITL] 內建 AI 授權執行動作的 Session State
# recommended_action: 儲存 AI 建議的執行動作字典（從任務狀態 API 回傳）
# action_executed:    防呄旗標，一旦執行即設為 True，避免重複發送請求
if "ai_recommended_action" not in st.session_state:
    st.session_state["ai_recommended_action"] = None
if "ai_action_executed" not in st.session_state:
    st.session_state["ai_action_executed"] = False
if "ai_action_result" not in st.session_state:
    st.session_state["ai_action_result"] = None

def load_ehs_scenario():
    st.session_state["sim_carbon"] = 1.65
    st.session_state["sim_yield"] = 92.5
    st.session_state["sim_user"] = "EHS_Monitor"
    st.session_state["sim_dept"] = "製造一部"
    st.session_state["sim_shift"] = "A班"
    st.session_state["sim_equip"] = "BOILER-01"
    st.session_state["sim_log"] = "EHS系統偵測：碳排放強度（1.65 kgCO₂e/unit）超標，觸發 ISO 14064-1 稽核程序。"

def load_mes_scenario():
    st.session_state["sim_carbon"] = 0.85
    st.session_state["sim_yield"] = 79.3
    st.session_state["sim_user"] = "生管主管"
    st.session_state["sim_dept"] = "品保部"
    st.session_state["sim_shift"] = "B班"
    st.session_state["sim_equip"] = "SMT-LINE-03"
    st.session_state["sim_log"] = "MES系統通報：製程良率大跌至 79.3%，低於標準門檻 85%，觸發 SOP-PROD-001 生產稽核。"

def load_siem_scenario():
    st.session_state["sim_carbon"] = 0.50
    st.session_state["sim_yield"] = 99.1
    st.session_state["sim_user"] = "unknown.user"
    st.session_state["sim_dept"] = "資安部"
    st.session_state["sim_shift"] = "C班"
    st.session_state["sim_equip"] = "SERVER-SEC-01"
    st.session_state["sim_log"] = "SIEM資安告警：偵測到深夜異常大量下載機密合規資產，來源IP 192.168.1.105，觸發 ISO 27001 A.8.16 審計。"

# 使用 st.session_state 控管模擬狀態
if "sim_active" not in st.session_state:
    st.session_state["sim_active"] = False
if "sim_thread" not in st.session_state:
    st.session_state["sim_thread"] = None
if "sim_stop_event" not in st.session_state:
    st.session_state["sim_stop_event"] = None

def bombard_worker(stop_event):
    import requests
    import time
    import random
    import os
    
    backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")
    api_url = f"{backend_url}/api/v1/trigger_audit"
    scenarios = [
        {
            "carbon_intensity": 1.65,
            "user_id": "EHS_Monitor",
            "event_log": "EHS系統偵測：碳排放強度（1.65 kgCO₂e/unit）超標，觸發 ISO 14064-1 稽核程序。",
            "department": "製造一部",
            "shift": "A班",
            "equipment_id": "BOILER-01",
            "production_yield": 92.5
        },
        {
            "carbon_intensity": 0.85,
            "user_id": "生管主管",
            "event_log": "MES系統通報：製程良率大跌至 79.3%，低於標準門檻 85%，觸發 SOP-PROD-001 生產稽核。",
            "department": "品保部",
            "shift": "B班",
            "equipment_id": "SMT-LINE-03",
            "production_yield": 79.3
        },
        {
            "carbon_intensity": 0.50,
            "user_id": "unknown.user",
            "event_log": "SIEM資安告警：偵測到深夜異常下載機密合規資產，來源IP 192.168.1.105，觸發 ISO 27001 A.8.16 審計。",
            "department": "資安部",
            "shift": "C班",
            "equipment_id": "SERVER-SEC-01",
            "production_yield": 99.1
        }
    ]
    
    while not stop_event.is_set():
        try:
            scenario = random.choice(scenarios).copy()
            if scenario["user_id"] == "EHS_Monitor":
                scenario["carbon_intensity"] = round(random.uniform(1.2, 2.5), 2)
            elif scenario["user_id"] == "生管主管":
                scenario["production_yield"] = round(random.uniform(65.0, 84.0), 1)
            requests.post(api_url, json=scenario, timeout=3)
        except Exception:
            pass
        
        # 循環偵測 300 秒 (5 分鐘)，如果期間 stop_event 被設定則立即中斷，避免線程卡死
        for _ in range(300):
            if stop_event.is_set():
                break
            time.sleep(1)

# ── 頁面基本設定 ─────────────────────────────────────────────
st.set_page_config(
    page_title="企業數位韌性 AI 導航系統",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# [FEATURE] Docker 容器化：支援環境變數讀取後端 URL
BACKEND = os.getenv("BACKEND_URL", "http://localhost:8000")

# ── 自定義 CSS ───────────────────────────────────────────────
st.markdown("""
<style>
    /* 強制隱藏 Streamlit 預設裝飾 */
    header { visibility: hidden !important; }
    footer { visibility: hidden !important; }
    #MainMenu { visibility: hidden !important; }
    .stDeployButton { display: none !important; }
    
    /* 全局背景色與文字 */
    body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background-color: #0A1128 !important;
        color: #FFFFFF !important;
        font-family: 'Outfit', 'Noto Sans TC', sans-serif !important;
    }
    
    /* 調整側邊欄樣式 */
    [data-testid="stSidebar"] {
        background-color: #060B1E !important;
        border-right: 1px solid #1E295D !important;
    }
    
    /* 統一 st.markdown 容器圓角邊框 (Card Container) */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #111936 !important;
        border: 1px solid #1E295D !important;
        border-radius: 6px !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4) !important;
    }
    
    /* 自訂戰情室卡片樣式 */
    .metric-card {
        background-color: #111936;
        border: 1px solid #1E295D;
        border-radius: 6px;
        padding: 16px 20px;
        text-align: left;
        color: #FFFFFF;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
        position: relative;
        overflow: hidden;
        margin-bottom: 12px;
    }
    .metric-card::before {
        content: '';
        position: absolute;
        left: 0;
        top: 0;
        bottom: 0;
        width: 4px;
        background-color: #00D2D3;
    }
    
    /* 警示級別霓虹左側邊條 */
    .metric-card-severe::before { background-color: #FF4D4D; box-shadow: 0 0 10px #FF4D4D; }
    .metric-card-warning::before { background-color: #FFA934; box-shadow: 0 0 10px #FFA934; }
    .metric-card-success::before { background-color: #2ED573; box-shadow: 0 0 10px #2ED573; }
    .metric-card-info::before { background-color: #22A6B3; box-shadow: 0 0 10px #22A6B3; }
    
    .metric-label {
        font-size: 0.8rem;
        color: #8A99AD;
        font-weight: 500;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }
    .metric-value {
        font-size: 2.2rem;
        font-weight: 700;
        margin: 4px 0;
        line-height: 1.2;
    }
    .metric-sub {
        font-size: 0.75rem;
        color: #64748B;
    }
    
    /* 微型標籤/徽章 */
    .badge-mini {
        position: absolute;
        right: 12px;
        top: 12px;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 0.7rem;
        font-weight: 600;
    }
    .badge-mini-red { background: rgba(255, 77, 77, 0.15); color: #FF4D4D; border: 1px solid rgba(255, 77, 77, 0.3); }
    .badge-mini-yellow { background: rgba(255, 169, 52, 0.15); color: #FFA934; border: 1px solid rgba(255, 169, 52, 0.3); }
    .badge-mini-green { background: rgba(46, 213, 115, 0.15); color: #2ED573; border: 1px solid rgba(46, 213, 115, 0.3); }
    .badge-mini-cyan { background: rgba(0, 210, 211, 0.15); color: #00D2D3; border: 1px solid rgba(0, 210, 211, 0.3); }
    
    /* AI 霓虹控制台卡片 */
    .ai-console-card {
        background-color: #111936;
        border: 1px solid #00D2D3;
        border-radius: 6px;
        padding: 20px;
        box-shadow: 0 0 15px rgba(0, 210, 211, 0.15);
        position: relative;
    }
    .ai-latency-tag {
        font-size: 0.7rem;
        color: #00D2D3;
        opacity: 0.8;
        text-align: right;
        margin-top: 8px;
    }
    
    /* 狀態標籤 */
    .badge-safe     { background:#2ED57320; color:#2ED573; padding:4px 12px; border-radius:20px; font-size:0.8rem; border:1px solid #2ED57340; }
    .badge-warn     { background:#FFA93420; color:#FFA934; padding:4px 12px; border-radius:20px; font-size:0.8rem; border:1px solid #FFA93440; }
    .badge-critical { background:#FF4D4D20; color:#FF4D4D; padding:4px 12px; border-radius:20px; font-size:0.8rem; border:1px solid #FF4D4D40; }
    
    /* 報告區塊樣式 */
    .report-box {
        background-color: #060B1E;
        border: 1px solid #1E295D;
        border-radius: 6px;
        padding: 16px 20px;
        color: #E2E8F0;
        font-family: 'Outfit', 'Noto Sans TC', sans-serif;
        line-height: 1.7;
        white-space: pre-wrap;
        font-size: 0.95rem;
    }
    
    /* 表格視覺優化 */
    div[data-testid="stTable"] table {
        background-color: #111936 !important;
        color: #FFFFFF !important;
        border-collapse: collapse;
        border: 1px solid #1E295D !important;
        width: 100%;
    }
    div[data-testid="stTable"] th {
        background-color: #162047 !important;
        color: #00D2D3 !important;
        font-weight: 600;
        border: 1px solid #1E295D !important;
        padding: 10px;
        text-align: left;
    }
    div[data-testid="stTable"] td {
        border: 1px solid #1E295D !important;
        padding: 8px 10px;
    }
    div[data-testid="stTable"] tr:nth-child(even) {
        background-color: #151E3D !important; /* 斑馬紋 */
    }
    div[data-testid="stTable"] tr:hover {
        background-color: #1E2A5C !important; /* 懸停 */
        transition: background-color 0.2s ease;
    }

    /* [Step 5 ESG] ESG 碳排預警卡片樣式：使用 #2ED573 綠色霧光系表示環境維度指標 */
    .esg-card {
        background: linear-gradient(135deg, #0A1E12 0%, #111936 100%);
        border: 1px solid #2ED573;
        border-radius: 6px;
        padding: 16px 20px;
        text-align: left;
        color: #FFFFFF;
        box-shadow: 0 0 18px rgba(46, 213, 115, 0.18), 0 4px 15px rgba(0, 0, 0, 0.3);
        position: relative;
        overflow: hidden;
        margin-bottom: 12px;
    }
    /* ESG 卡片左側標誌條 */
    .esg-card::before {
        content: '';
        position: absolute;
        left: 0;
        top: 0;
        bottom: 0;
        width: 4px;
        background: linear-gradient(180deg, #2ED573, #00D2D3);
        box-shadow: 0 0 12px rgba(46, 213, 115, 0.8);
    }
    /* ESG 卡片頁簽 */
    .esg-label {
        font-size: 0.75rem;
        color: #2ED573;
        font-weight: 600;
        letter-spacing: 0.06em;
        text-transform: uppercase;
    }
    .esg-value {
        font-size: 2.0rem;
        font-weight: 700;
        color: #2ED573;
        margin: 4px 0;
        line-height: 1.2;
    }
    .esg-sub {
        font-size: 0.72rem;
        color: #7FC99B;
    }
    /* ESG 告警列表：高亮字欲 */
    .esg-alert-badge {
        background: rgba(46, 213, 115, 0.12);
        color: #2ED573;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 0.78rem;
        border: 1px solid rgba(46, 213, 115, 0.35);
        display: inline-block;
        font-weight: 600;
    }

    /* ====== Agentic Action 授權按鈕樣式 ====== */
    /* 微發光瘩色按鈕：符合 Dark Mode 審美，與 AI 小控台卡片協調 */
    .btn-authorize-action {
        display: inline-block;
        width: 100%;
        padding: 12px 20px;
        margin-top: 12px;
        background: linear-gradient(135deg, #1a1200 0%, #2d1f00 100%);
        border: 1px solid #F59E0B;
        border-radius: 8px;
        color: #FCD34D;
        font-size: 1.0rem;
        font-weight: 700;
        font-family: 'Outfit', 'Noto Sans TC', sans-serif;
        text-align: center;
        cursor: pointer;
        letter-spacing: 0.03em;
        box-shadow:
            0 0 12px rgba(245, 158, 11, 0.25),
            0 0 24px rgba(245, 158, 11, 0.10),
            inset 0 1px 0 rgba(255, 255, 255, 0.05);
        transition: all 0.25s ease;
        text-decoration: none;
    }
    .btn-authorize-action:hover {
        background: linear-gradient(135deg, #2d1f00 0%, #3d2a00 100%);
        border-color: #FCD34D;
        box-shadow:
            0 0 20px rgba(245, 158, 11, 0.45),
            0 0 40px rgba(245, 158, 11, 0.20),
            inset 0 1px 0 rgba(255, 255, 255, 0.08);
        color: #FDE68A;
    }
    /* 執行成功狀態樣式：綠色微發光 */
    .action-success-badge {
        background: linear-gradient(135deg, #0a1e0f 0%, #0d2016 100%);
        border: 1px solid #2ED573;
        border-radius: 8px;
        padding: 14px 18px;
        color: #2ED573;
        font-size: 0.95rem;
        font-weight: 600;
        margin-top: 12px;
        box-shadow: 0 0 15px rgba(46, 213, 115, 0.20);
        text-align: center;
        line-height: 1.6;
    }
    /* 執行資訊明細卡 */
    .action-detail-card {
        background: rgba(46, 213, 115, 0.05);
        border: 1px solid rgba(46, 213, 115, 0.2);
        border-radius: 6px;
        padding: 10px 14px;
        margin-top: 8px;
        font-size: 0.82rem;
        color: #94a3b8;
        line-height: 1.6;
    }
    .action-detail-card strong { color: #CBD5E1; }
</style>
""", unsafe_allow_html=True)


# ╔══════════════════════════════════════════════════════════╗
# ║  工具函式                                                ║
# ╚══════════════════════════════════════════════════════════╝

def api_get(path: str) -> dict | None:
    try:
        headers = {}
        if "token" in st.session_state and st.session_state["token"]:
            headers["Authorization"] = f"Bearer {st.session_state['token']}"
        r = requests.get(f"{BACKEND}{path}", headers=headers, timeout=5)
        return r.json()
    except Exception:
        return None

def api_post(path: str, data: dict) -> dict | None:
    try:
        headers = {}
        if "token" in st.session_state and st.session_state["token"]:
            headers["Authorization"] = f"Bearer {st.session_state['token']}"
        r = requests.post(f"{BACKEND}{path}", json=data, headers=headers, timeout=10)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

def risk_color(level: int) -> str:
    return {1: "#16a34a", 2: "#d97706", 3: "#dc2626"}.get(level, "#64748b")

def carbon_gauge_emoji(value: float) -> str:
    if value <= 1.0:  return "🟢"
    if value <= 1.5:  return "🟡"
    if value <= 2.0:  return "🟠"
    return "🔴"


# ╔══════════════════════════════════════════════════════════╗
# ║  側邊欄：系統設定                                        ║
# ╚══════════════════════════════════════════════════════════╝

@st.cache_data(ttl=15)
def get_cached_detailed_health() -> dict | None:
    try:
        headers = {}
        if "token" in st.session_state and st.session_state["token"]:
            headers["Authorization"] = f"Bearer {st.session_state['token']}"
        r = requests.get(f"{BACKEND}/api/health/detailed", headers=headers, timeout=2.0)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None

with st.sidebar:
    st.markdown("## 🛡️ 系統控制台")
    st.divider()

    # 顯示登入身分與登出
    st.markdown("### 👤 當前使用者")
    st.success(f"帳號角色: **{st.session_state.role}**")
    if st.button("🚪 登出系統", use_container_width=True):
        st.session_state["token"] = None
        st.session_state["role"] = None
        st.rerun()

    st.divider()

    # 呼叫 /api/health/detailed 監測系統健康狀態並使用快取防卡頓
    detailed_health = get_cached_detailed_health()

    # 1. 地端大腦狀態
    st.markdown("### 🧠 地端大腦狀態")
    if detailed_health and detailed_health.get("ollama") == "online":
        st.success("🟢 Ollama 在線 (Online)")
    else:
        st.error("🔴 Ollama 離線 (Offline)")
        if st.button("🔄 重新連線 Ollama", key="reconnect_ollama_btn", use_container_width=True):
            get_cached_detailed_health.clear()
            st.rerun()

    st.divider()

    # 2. 子系統狀態
    if detailed_health:
        st.markdown("### 📡 子系統狀態")
        st.metric("進行中稽核", detailed_health.get("active_tasks", 0))
        st.markdown("🟢 **API**: `online`")
        chroma_val = detailed_health.get("chromadb", "offline")
        chroma_color = "🟢" if "online" in str(chroma_val) else "🔴"
        st.markdown(f"{chroma_color} **CHROMADB**: `{chroma_val}`")
    else:
        st.markdown("### 📡 子系統狀態")
        st.error("❌ 無法連線後端 API\n請確認 FastAPI 已啟動於 :8000")

    st.divider()
    st.markdown("### ⚙️ AI 模型設定")
    st.info("🤖 **qwen2.5:14b**\n運行於本地 Ollama\nPort: 11434")

    st.divider()
    st.markdown("### 🔄 自動刷新")
    auto_refresh = st.toggle("啟用每 30 秒自動刷新", value=False)
    if auto_refresh:
        st.info("系統將自動更新數據")
        time.sleep(30)
        st.rerun()

    st.divider()

    # 3. 詳細系統健康面板
    if detailed_health:
        st.markdown("### 📊 資料庫統計")
        db_s = detailed_health.get("db_stats", {})
        col_s1, col_s2 = st.columns(2)
        col_s1.metric("📋 總報告數", db_s.get("total_reports", 0))
        col_s2.metric("✅ 已完成",   db_s.get("completed_reports", 0))
        col_s3, col_s4 = st.columns(2)
        col_s3.metric("⏳ 待審核",   db_s.get("pending_approval", 0))
        col_s4.metric("📅 今日稽核", db_s.get("today_reports", 0))

        q_depth = detailed_health.get("task_queue_depth", 0)
        if q_depth > 0:
            st.warning(f"🔄 AI 佇列深度：{q_depth} 筆等待中")
        else:
            st.success("🔄 AI 佇列：閒置 (Idle)")
        st.markdown(f"`SQLite:` {detailed_health.get('sqlite', 'unknown')}")

    # [Step 5] 報表中心 (僅限 admin 與 ciso)
    if st.session_state.get("role") in ["admin", "ciso"]:
        st.divider()
        st.markdown("### 📊 報表中心")
        with st.container(border=True):
            st.markdown("##### 📥 稽核週報一鍵匯出")
            st.caption("自動彙整近 7 日稽核軌跡，由 AI 撰寫合規摘要並輸出 Word。")
            if st.button("🔄 生成本週 AI 稽核報告", use_container_width=True, key="btn_trigger_weekly_report"):
                with st.spinner("🚀 正在撈取日誌並呼叫 AI 產生查核報告..."):
                    try:
                        headers = {}
                        if "token" in st.session_state and st.session_state["token"]:
                            headers["Authorization"] = f"Bearer {st.session_state['token']}"
                        r = requests.get(f"{BACKEND}/api/reports/generate", headers=headers, timeout=35)
                        if r.status_code == 200:
                            st.session_state["weekly_report_bytes"] = r.content
                            st.success("🟢 報告生成成功！")
                        elif r.status_code == 403:
                            st.error("❌ 權限不足：限 admin/ciso 下載")
                        else:
                            st.error(f"❌ 生成失敗 ({r.status_code})：{r.text}")
                    except Exception as e:
                        st.error(f"❌ 連線後端報表 API 失敗：{e}")

            if "weekly_report_bytes" in st.session_state and st.session_state["weekly_report_bytes"]:
                today_filename = datetime.now().strftime("%Y%m%d")
                st.download_button(
                    label="📥 下載 Word 稽核報告 (.docx)",
                    data=st.session_state["weekly_report_bytes"],
                    file_name=f"Audit_Report_{today_filename}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True,
                    key="btn_download_weekly_report"
                )

    st.divider()
    st.caption(f"🕐 最後更新：{datetime.now().strftime('%H:%M:%S')}")
    st.caption("© 2025 企業數位韌性系統 v2.0")


# ╔══════════════════════════════════════════════════════════╗
# ║  主頁面                                                  ║
# ╚══════════════════════════════════════════════════════════╝

st.markdown("# 🛡️ 企業數位韌性 AI 導航系統")
st.markdown("**地端安全私有化 AI 決策中樞** ｜ ISO 14064-1 × ISO 27001 × 生管 SOP 三合一合規稽核")
st.divider()

role = st.session_state.role
token = st.session_state.token

# [DEMO FEATURE] 快速情境展示
with st.expander("🎬 快速情境展示", expanded=True):
    st.markdown("點擊下方按鈕以發送情境模擬數據至後端，並自動觸發非同步 AI 稽核流程：")
    col_demo1, col_demo2, col_demo3 = st.columns(3)
    
    # 嘗試從後端 API 取得 Mock Data 配置
    scenarios_data = api_get("/api/v1/scenarios")
    if not scenarios_data:
        # Fallback 備份配置，確保後端未就緒時網頁不崩潰
        scenarios_data = {
            "scenario_1": {
                "carbon_intensity": 0.52,
                "user_id": "EMP-1024",
                "event_log": "生產線警報：C線 SMT 區發生製程異常，當班良率自平均 98.5% 急遽跌至 82.1%，低於公司內部合規標準門檻 85%，觸發 SOP-PROD-001 生產合規稽核流程。",
                "department": "生產部-SMT區",
                "shift": "A班",
                "equipment_id": "SMT-LINE-C",
                "production_yield": 82.1
            },
            "scenario_2": {
                "carbon_intensity": 0.45,
                "user_id": "unknown.user",
                "event_log": "SIEM資安告警：於凌晨 02:30 偵測到研發伺服器遭受來自海外不明來源之 15 次連續登入失敗嘗試，隨後有高達 5GB 的敏感專利代碼與合規文件遭異常下載導出，觸發 ISO 27001 A.8.16 資訊安全事件響應與審計。",
                "department": "研發部",
                "shift": "C班",
                "equipment_id": "SERVER-RND-01",
                "production_yield": 99.8
            },
            "scenario_3": {
                "carbon_intensity": 24.75,
                "user_id": "EHS_Auditor",
                "event_log": "EHS系統警報：二廠當日電力消耗高達 50 萬度，合計產出 1 萬件產品，換算碳排放強度達 24.75 kgCO₂e/unit，已超標 15%，觸發 ISO 14064-1 溫室氣體盤查與矯正預警程序。",
                "department": "製造二廠",
                "shift": "B班",
                "equipment_id": "FACTORY-02",
                "production_yield": 98.2
            }
        }
    
    if col_demo1.button("情境一：生管異常", use_container_width=True):
        st.toast("正在發送情境數據至後端...", icon="🎬")
        result = api_post("/api/v1/trigger_audit", scenarios_data.get("scenario_1"))
        if result and "task_id" in result:
            st.session_state["demo_task_id"] = result["task_id"]
            st.session_state["demo_status"] = "polling"
            st.session_state["demo_report"] = None
            st.rerun()
        else:
            st.error(f"觸發失敗: {result}")
            
    if col_demo2.button("情境二：資安威脅", use_container_width=True):
        st.toast("正在發送情境數據至後端...", icon="🎬")
        result = api_post("/api/v1/trigger_audit", scenarios_data.get("scenario_2"))
        if result and "task_id" in result:
            st.session_state["demo_task_id"] = result["task_id"]
            st.session_state["demo_status"] = "polling"
            st.session_state["demo_report"] = None
            st.rerun()
        else:
            st.error(f"觸發失敗: {result}")
            
    if col_demo3.button("情境三：碳排超標", use_container_width=True):
        st.toast("正在發送情境數據至後端...", icon="🎬")
        result = api_post("/api/v1/trigger_audit", scenarios_data.get("scenario_3"))
        if result and "task_id" in result:
            st.session_state["demo_task_id"] = result["task_id"]
            st.session_state["demo_status"] = "polling"
            st.session_state["demo_report"] = None
            st.rerun()
        else:
            st.error(f"觸發失敗: {result}")

# [DEMO FEATURE] 當前模擬情境處理狀態顯示區 (Polling & Results Display)
if st.session_state["demo_task_id"] is not None:
    st.markdown("---")
    st.markdown(f"### 📍 當前情境處理狀態顯示區 (Task ID: `{st.session_state['demo_task_id']}`)")
    
    if st.session_state["demo_status"] == "polling":
        with st.status("🔄 正在進行非同步 AI 檢索與推理...") as status_box:
            task_id = st.session_state["demo_task_id"]
            report = None
            for i in range(30):
                time.sleep(2)
                report = api_get(f"/api/task/{task_id}")
                if report:
                    current_status = report.get("status")
                    if current_status == "processing":
                        status_box.update(label=f"正在進行 AI 檢索與推理... ({(i+1)*2}秒)", state="running")
                    elif current_status == "completed":
                        status_box.update(label="AI 稽核與推理完成！", state="complete", expanded=True)
                        st.session_state["demo_status"] = "completed"
                        st.session_state["demo_report"] = report
                        break
                    elif current_status == "pending_approval":
                        status_box.update(label="AI 稽核完成，等待審核！", state="complete", expanded=True)
                        st.session_state["demo_status"] = "pending_approval"
                        st.session_state["demo_report"] = report
                        break
                    elif current_status == "failed":
                        status_box.update(label="AI 稽核與推理失敗！", state="error", expanded=True)
                        st.session_state["demo_status"] = "failed"
                        st.session_state["demo_report"] = report
                        break
                else:
                    status_box.update(label="無法獲取後端狀態，正在重試...", state="running")
            
            if st.session_state["demo_status"] == "polling":
                status_box.update(label="AI 稽核處理超時，請稍後至歷史報告中查看", state="error", expanded=True)
                st.session_state["demo_status"] = "failed"
            st.rerun()
            
    elif st.session_state["demo_status"] in ["completed", "failed", "pending_approval", "rejected"]:
        report = st.session_state["demo_report"]
        
        # [FEATURE] HITL 審核機制：待審批狀態顯示
        if report and report.get("status") == "pending_approval":
            risk = report.get("risk_assessment", {})
            risk_lv = risk.get("risk_level", 1)
            risk_lbl = risk.get("risk_label", "Level-1 輕微")
            reasons = risk.get("reasons", [])
            resp_time = risk.get("response_time", "")
            
            with st.container(border=True):
                col_title, col_btn = st.columns([5, 1])
                col_title.markdown(f"#### 🔒 待審核稽核報告 (Task ID: `{st.session_state['demo_task_id']}`)")
                if col_btn.button("🗑️ 關閉展示結果", use_container_width=True, key="close_pending"):
                    st.session_state["demo_task_id"] = None
                    st.session_state["demo_status"] = "idle"
                    st.session_state["demo_report"] = None
                    st.rerun()
                    
                st.warning("⚠️ [FEATURE] HITL 審核機制：此任務包含重大決策，需要管理階層審核後方可執行 Agent 行動。")
                st.divider()
                
                # 1. [AI 診斷結果]
                st.markdown("### 📊 [AI 診斷結果]")
                if risk_lv == 3:
                    st.error(f"**風險級別：{risk_lbl}**")
                elif risk_lv == 2:
                    st.warning(f"**風險級別：{risk_lbl}**")
                else:
                    st.success(f"**風險級別：{risk_lbl}**")
                
                col_res1, col_res2 = st.columns([3, 2])
                with col_res1:
                    st.markdown("**判定原因：**")
                    for r in reasons:
                        st.markdown(f"- ⚠️ {r}")
                with col_res2:
                    st.markdown("**要求回應時限：**")
                    st.info(f"⏱️ {resp_time}")
                
                st.divider()
                
                # 2. [預計執行的 Agent 動作]
                st.markdown("### 🤖 [預計執行的 Agent 動作]")
                proposed_action = report.get("proposed_action", "")
                if proposed_action:
                    st.info(f"{proposed_action}")
                else:
                    st.info("無擬定之 Agent 模擬防禦或通報動作。")
                
                st.divider()
                
                # 3. [生成之 CAPA 報告]
                st.markdown("### 📄 [AI 草擬之 CAPA 報告]")
                st.markdown(
                    f'<div class="report-box">{report.get("ai_capa_report", "")}</div>',
                    unsafe_allow_html=True
                )
                
                st.divider()
                
                # 審核表單
                st.markdown("### ✍️ 人工審核 (Human-in-the-Loop)")
                approver = st.text_input("審核人主管姓名 / 員編 ID", value="CISO_Manager", key="hitl_approver")
                
                col_app, col_rej = st.columns(2)
                if col_app.button("✅ 核准並執行 (Approve & Execute)", type="primary", use_container_width=True):
                    res = api_post(f"/api/task/{st.session_state['demo_task_id']}/approve", {"approver": approver})
                    if res and res.get("status") == "completed":
                        st.toast("✅ 核准成功！Agent 行動已觸發執行。", icon="🚀")
                        st.session_state["demo_status"] = "completed"
                        st.session_state["demo_report"] = res
                        st.rerun()
                    else:
                        st.error(f"核准執行失敗：{res}")
                        
                if col_rej.button("❌ 退回重擬 (Reject)", type="secondary", use_container_width=True):
                    res = api_post(f"/api/task/{st.session_state['demo_task_id']}/reject", {"rejected_by": approver, "reason": "退回重擬"})
                    if res and res.get("status") == "rejected":
                        st.toast("❌ 稽核報告已退回重擬。", icon="↩️")
                        st.session_state["demo_status"] = "rejected"
                        st.session_state["demo_report"] = res
                        st.rerun()
                    else:
                        st.error(f"退回失敗：{res}")

        # [FEATURE] HITL 審核機制：退回狀態顯示
        elif report and report.get("status") == "rejected":
            with st.container(border=True):
                col_title, col_btn = st.columns([5, 1])
                col_title.markdown(f"#### ❌ 稽核報告已退回 (Task ID: `{st.session_state['demo_task_id']}`)")
                if col_btn.button("🗑️ 關閉展示結果", use_container_width=True, key="close_rejected"):
                    st.session_state["demo_task_id"] = None
                    st.session_state["demo_status"] = "idle"
                    st.session_state["demo_report"] = None
                    st.rerun()
                
                st.error(f"🔴 此稽核報告已被 **{report.get('rejected_by')}** 退回重擬。")
                st.info(f"💬 退回原因：{report.get('reject_reason', '無')}")
                
                st.divider()
                
                # 3. [生成之 CAPA 報告]
                st.markdown("### 📄 [退回之 CAPA 報告草稿]")
                st.markdown(
                    f'<div class="report-box">{report.get("ai_capa_report", "")}</div>',
                    unsafe_allow_html=True
                )

        elif report and report.get("status") == "completed":
            risk = report.get("risk_assessment", {})
            risk_lv = risk.get("risk_level", 1)
            risk_lbl = risk.get("risk_label", "Level-1 輕微")
            reasons = risk.get("reasons", [])
            resp_time = risk.get("response_time", "")
            
            with st.container(border=True):
                col_title, col_btn = st.columns([5, 1])
                col_title.markdown(f"#### 🎬 模擬情境結果展示 (Task ID: `{st.session_state['demo_task_id']}`)")
                if col_btn.button("🗑️ 關閉展示結果", use_container_width=True, key="close_completed"):
                    st.session_state["demo_task_id"] = None
                    st.session_state["demo_status"] = "idle"
                    st.session_state["demo_report"] = None
                    st.rerun()
                    
                st.divider()
                
                # 1. [AI 診斷結果]
                st.markdown("### 📊 [AI 診斷結果]")
                if risk_lv == 3:
                    st.error(f"**風險級別：{risk_lbl}**")
                elif risk_lv == 2:
                    st.warning(f"**風險級別：{risk_lbl}**")
                else:
                    st.success(f"**風險級別：{risk_lbl}**")
                
                col_res1, col_res2 = st.columns([3, 2])
                with col_res1:
                    st.markdown("**判定原因：**")
                    for r in reasons:
                        st.markdown(f"- ⚠️ {r}")
                with col_res2:
                    st.markdown("**要求回應時限：**")
                    st.info(f"⏱️ {resp_time}")
                
                st.divider()
                
                # 2. [Agent 執行動作]
                st.markdown("### 🤖 [Agent 執行動作]")
                agent_action = report.get("agent_notification")
                if agent_action:
                    st.info(f"{agent_action}")
                else:
                    st.info("無觸發任何 Agent 模擬防禦或通報動作。")
                
                st.divider()
                
                # 3. [生成之 CAPA 報告]
                st.markdown("### 📄 [生成之 CAPA 報告]")
                st.markdown(
                    f'<div class="report-box">{report.get("ai_capa_report", "")}</div>',
                    unsafe_allow_html=True
                )
                
                # [FEATURE] 匯出正式報告功能
                st.divider()
                st.markdown("### 📥 報告匯出")
                try:
                    export_task_id = st.session_state['demo_task_id']
                    headers = {}
                    if "token" in st.session_state and st.session_state["token"]:
                        headers["Authorization"] = f"Bearer {st.session_state['token']}"
                    res = requests.get(f"{BACKEND}/api/task/{export_task_id}/export", headers=headers, timeout=5)
                    if res.status_code == 200:
                        st.download_button(
                            label="📥 下載官方 ISO 改善對策報告 (Word)",
                            data=res.content,
                            file_name=f"ISO_Audit_Report_{export_task_id}.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            use_container_width=True,
                            key="btn_export_completed"
                        )
                    else:
                        st.error("⚠️ 無法從後端取得 Word 改善報告")
                except Exception as e:
                    st.error(f"⚠️ 讀取 Word 報告出錯：{e}")
                
        elif report and report.get("status") == "failed":
            st.error(f"❌ 模擬稽核失敗：{report.get('error')}")
            if st.button("🗑️ 關閉結果", key="close_failed"):
                st.session_state["demo_task_id"] = None
                st.session_state["demo_status"] = "idle"
                st.session_state["demo_report"] = None
                st.rerun()
    st.markdown("---")

# 頁籤導覽
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 即時監控 Dashboard",
    "🚨 手動觸發稽核",
    "📋 歷史報告查閱",
    "🧠 系統架構說明"
])


# ─── Tab 1：即時監控 Dashboard ───────────────────────────────
with tab1:
    st.markdown("## 📊 產線即時狀態（模擬 Power BI 數據饋入）")
    st.caption("數據來源：MES 系統 Webhook → FastAPI 後端 → 去識別化 → AI 分析")

    # [Step 5 ESG] 頂部指標區：5 欄配置（前 4 欄套用原樣式，第 5 欄新增 ESG 碳排預警卡片）
    col1, col2, col3, col4, col_esg = st.columns([1, 1, 1, 1, 1])

    # [Step 4] 動態讀取報告數據計算 KPI
    _all_reports = api_get("/api/v1/reports") or []
    _today_str   = datetime.now().strftime("%Y-%m-%d")
    _today_done  = sum(1 for r in _all_reports if r.get("status") == "completed"
                       and (_today_str in (r.get("created_at") or "")))
    _pending_cnt = sum(1 for r in _all_reports if r.get("status") == "pending_approval")
    _max_risk    = max((r.get("risk_level", 1) for r in _all_reports), default=1)
    _total_cnt   = len(_all_reports)

    # 定義 _high_risk_reports 以解決 NameError 告警事件錯誤
    _high_risk_reports = []
    for r in _all_reports:
        if r.get("risk_level", 1) >= 2:
            if "risk_label" not in r and "risk_level" in r:
                lv = r.get("risk_level", 1)
                r["risk_label"] = {1: "Level-1 輕微", 2: "Level-2 嚴重", 3: "Level-3 緊急"}.get(lv, f"Level-{lv}")
            _high_risk_reports.append(r)

    # KPI 色彩映射
    _risk_color_map = {1: "metric-card-success", 2: "metric-card-warning", 3: "metric-card-severe"}
    _risk_label_map = {1: "🟢 正常", 2: "🟡 警示", 3: "🔴 緊急"}
    _risk_badge_map = {1: "badge-mini-green", 2: "badge-mini-yellow", 3: "badge-mini-red"}
    _max_risk_cls   = _risk_color_map.get(_max_risk, "metric-card-info")
    _max_risk_lbl   = _risk_label_map.get(_max_risk, "未知")
    _max_risk_bdg   = _risk_badge_map.get(_max_risk, "badge-mini-cyan")

    with col1:
        st.markdown(f"""
        <div class="metric-card metric-card-info">
            <span class="badge-mini badge-mini-cyan">📋 所有</span>
            <div class="metric-label">總稽核報告數</div>
            <div class="metric-value" style="color:#00D2D3">{_total_cnt}</div>
            <div class="metric-sub">SQLite 持久化儲存</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-card metric-card-success">
            <span class="badge-mini badge-mini-green">✅ 今日</span>
            <div class="metric-label">今日完成稽核</div>
            <div class="metric-value" style="color:#2ED573">{_today_done}</div>
            <div class="metric-sub">已核准並歸檔</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        _pending_color = "metric-card-warning" if _pending_cnt > 0 else "metric-card-success"
        _pending_badge = "badge-mini-yellow" if _pending_cnt > 0 else "badge-mini-green"
        _pending_icon  = "⏳ 待審" if _pending_cnt > 0 else "✅ 清空"
        st.markdown(f"""
        <div class="metric-card {_pending_color}">
            <span class="badge-mini {_pending_badge}">{_pending_icon}</span>
            <div class="metric-label">待人工審核</div>
            <div class="metric-value" style="color:#FFA934">{_pending_cnt}</div>
            <div class="metric-sub">HITL 簽核佇列</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="metric-card {_max_risk_cls}">
            <span class="badge-mini {_max_risk_bdg}">最高</span>
            <div class="metric-label">當前最高風險等級</div>
            <div class="metric-value" style="font-size:1.4rem;margin-top:6px">{_max_risk_lbl}</div>
            <div class="metric-sub">Level-{_max_risk} 事件存在</div>
        </div>
        """, unsafe_allow_html=True)


    # [Step 5 ESG] 第 5 欄：ESG 碳排預警卡片，使用 #2ED573 綠色系識別環境維度
    with col_esg:
        # 模擬本月廠區平均碳排放強度（生產環境中應從 EHS 系統 API 讀取）
        _avg_carbon = 1.45  # kgCO₂e/unit，模擬值
        _data_missing_count = 3  # 能耗數據缺漏件數，模擬值

        # 若有真實報告，略微調整模擬數字以顯示動態感
        if _all_reports:
            _completed_real = sum(1 for r in _all_reports if r.get("status") == "completed")
            # 真實完成筆數越多，缺漏件數遞減（模擬數據修復進度）
            _data_missing_count = max(0, 3 - _completed_real)

        # 碳排強度狀態判斷（顏色與文字）
        if _avg_carbon <= 1.0:
            _ci_color  = "#2ED573"
            _ci_icon   = "✅"
            _ci_status = "合規"
        elif _avg_carbon <= 1.5:
            _ci_color  = "#FFA934"
            _ci_icon   = "⚠️"
            _ci_status = "輕度超標"
        else:
            _ci_color  = "#FF4D4D"
            _ci_icon   = "🔴"
            _ci_status = "嚴重超標"

        st.markdown(f"""
        <div class="esg-card">
            <span style="position:absolute;right:12px;top:12px;background:rgba(46,213,115,0.15);
                color:#2ED573;border:1px solid rgba(46,213,115,0.3);padding:2px 6px;
                border-radius:4px;font-size:0.7rem;font-weight:600;">
                {_ci_icon} {_ci_status}
            </span>
            <div class="esg-label">🌱 ESG 碳排預警</div>
            <div class="esg-value" style="color:{_ci_color}">{_avg_carbon:.2f}</div>
            <div class="esg-sub">kgCO₂e/unit 本月均強度</div>
            <div style="margin-top:8px;font-size:0.72rem;color:#7FC99B;">
                📊 能耗缺漏: <strong style="color:#FFA934">{_data_missing_count}</strong> 件
                &nbsp;|&nbsp; Scope 2 查核中
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()


    # 左右大雙欄配置
    main_left, main_right = st.columns([3, 1])

    with main_left:
        st.markdown("### 📈 產線趨勢監控 (Realtime Trends)")
        
        # [Step 4] 動態趨勢圖：從真實報告中提取數據，無數據時使用模擬數據
        col_chart_a, col_chart_b = st.columns(2)
        with col_chart_a:
            st.markdown("##### 📈 碳排放強度趨勢（最近稽核）")
            _carbon_vals = [
                r.get("data_json") for r in _all_reports[:8]
                if r.get("data_json")
            ] if False else None  # DB列表不含data_json
            # 從 API 已有的 _all_reports 列表無法取到 carbon 數值，需用模擬數據
            carbon_data = pd.DataFrame({
                "班別":   ["A班-1", "B班-1", "C班-1", "A班-2", "B班-2", "C班-2", "A班-3", "B班-3"],
                "碳強度": [0.92, 1.05, 0.88, 1.23, 1.45, 1.31, 1.67, 1.45],
                "上限":   [1.0] * 8
            })
            st.line_chart(carbon_data.set_index("班別")[["碳強度", "上限"]])
            if _total_cnt > 0:
                st.caption(f"📊 系統已累積 **{_total_cnt}** 筆稽核記錄於 SQLite")

        with col_chart_b:
            st.markdown("##### 📊 稽核任務狀態分布")
            if _all_reports:
                _status_counts = {}
                for r in _all_reports:
                    s = r.get("status", "unknown")
                    _status_counts[s] = _status_counts.get(s, 0) + 1
                status_df = pd.DataFrame([
                    {"狀態": k, "數量": v}
                    for k, v in _status_counts.items()
                ])
                st.bar_chart(status_df.set_index("狀態"))
            else:
                yield_data = pd.DataFrame({
                    "班別": ["A班-1", "B班-1", "C班-1", "A班-2", "B班-2", "C班-2", "A班-3", "B班-3"],
                    "良率": [91.2, 88.5, 92.0, 85.3, 82.1, 79.3, 81.0, 79.3],
                    "目標": [85.0] * 8
                })
                st.line_chart(yield_data.set_index("班別")[["良率", "目標"]])
                st.caption("尚無稽核記錄，顯示模擬數據")

        st.divider()
        st.markdown("### 🚨 近期告警事件")
        # [Step 5 ESG] 在真實告警中插入 ESG 範疇二告警
        _esg_mock_alert = {
            "時間":   datetime.now().strftime("%H:%M"),
            "部門":   "SMT 第三廠區",
            "嚴重度": "🟢 Level-2 ESG",  # 綠色表示環境維度別
            "任務ID": "ESG-SCO2",
            "狀態":   "起源: SMT 設備能耗數據傳輸中斷 | 影響範疇二 (Scope 2) 盈查"
        }
        if _high_risk_reports:
            alerts = []
            for r in _high_risk_reports:
                _ts = (r.get("created_at") or "")[:16].replace("T", " ")
                _rl = r.get("risk_level", 1)
                _lbl = r.get("risk_label", "Level-1")
                _icon = "🔴" if _rl == 3 else "🟠"
                _dept = r.get("department", "未知部門")
                _tid  = r.get("task_id", "")
                alerts.append({
                    "時間":   _ts,
                    "部門":   _dept,
                    "嚴重度": f"{_icon} {_lbl}",
                    "任務ID": _tid[:8],
                    "狀態":   r.get("status", "")
                })
            # 將 ESG 告警插入列表首位
            alerts.insert(0, _esg_mock_alert)
            st.dataframe(pd.DataFrame(alerts), use_container_width=True, hide_index=True)
        else:
            # 無真實資料時顯示模擬告警
            alerts = [
                _esg_mock_alert,  # [Step 5] ESG 告警排在首位
                {"時間": "03:42", "部門": "研發部", "嚴重度": "🔴 Level-3", "任務ID": "SEC-001", "狀態": "深夜大量下載合規清冊（ISO 27001 A.8.16）"},
                {"時間": "06:15", "部門": "製造二廠", "嚴重度": "🟠 Level-2", "任務ID": "EHS-002", "狀態": "碳強度 1.67 超標（上限 1.0）"},
                {"時間": "08:30", "部門": "品保部", "嚴重度": "🟡 Level-2", "任務ID": "QMS-003", "狀態": "良率 79.3% 低於目標 85%"},
            ]
            st.dataframe(pd.DataFrame(alerts), use_container_width=True, hide_index=True)
            st.caption("⚠️ 尚無真實高風險告警，顯示模擬資料")

        # ── ISO 27001 內部審計稽核軌跡 (Audit Trail) - 限 admin / ciso ──
        if role in ["admin", "ciso"]:
            st.divider()
            st.markdown("### 📜 ISO 27001 內部審計稽核軌跡 (Audit Trail)")
            st.caption("此區域即時呈現 `audit.db` 資料庫內最新的 50 筆使用者操作與 AI 呼叫日誌。")
            
            if st.button("🔄 重新整理審計日誌", key="btn_refresh_audit_logs"):
                st.toast("審計軌跡已刷新")
            
            logs = api_get("/api/audit/logs")
            if logs is not None:
                if isinstance(logs, list):
                    if len(logs) > 0:
                        df_logs = pd.DataFrame(logs)
                        cols_order = ["timestamp", "username", "role", "action_type", "action_details", "prompt", "ai_response", "latency_ms"]
                        df_logs = df_logs[cols_order]
                        st.dataframe(df_logs, use_container_width=True, hide_index=True)
                    else:
                        st.info("📭 目前尚無審計日誌紀錄")
                else:
                    st.error(f"⚠️ 讀取日誌格式錯誤：{logs}")
            else:
                st.error("❌ 無法取得稽核日誌，請檢查後端服務與 Token")

    with main_right:
        st.markdown("### 📥 決策控制中心")
        
        # 待我處理簽核清單
        st.markdown("#### 📋 待我處理")
        has_pending = False
        
        # QMS 審核
        if role in ["admin", "qms_manager"]:
            has_pending = True
            with st.container(border=True):
                st.markdown("##### ⚙️ 品質管理系統 (QMS)")
                st.info("待簽核：SMT 製程良率異常 CAPA 矯正對策")
                if st.button("✅ 核准生管 CAPA (QMS)", key="btn_approve_qms", use_container_width=True, type="primary"):
                    st.success("🎉 生管 CAPA 已成功核准並歸檔！")
        
        # CISO 審核
        if role in ["admin", "ciso"]:
            has_pending = True
            with st.container(border=True):
                st.markdown("##### 🔒 資訊安全事件 (CISO)")
                st.info("待簽核：深夜異常專利外傳安全告警")
                if st.button("🚨 核准資安警報 (CISO)", key="btn_approve_ciso", use_container_width=True, type="primary"):
                    headers = {"Authorization": f"Bearer {token}"}
                    try:
                        with st.spinner("正在向後端 API 提交資安核准..."):
                             r = requests.post(f"{BACKEND}/api/audit/approve_sec", headers=headers, timeout=5)
                        if r.status_code == 200:
                            st.success(f"🟢 {r.json().get('message')}")
                            st.balloons()
                        elif r.status_code == 403:
                            st.error(f"❌ 權限不足！此操作已被安全中樞拒絕。")
                        else:
                            st.error(f"⚠️ 異常 ({r.status_code})：{r.text}")
                    except Exception as e:
                        st.error(f"❌ 連線後端 API 失敗：{e}")
                        
        if not has_pending:
            st.markdown("🔒 *您的身分目前無待簽核項目*")
            
        st.divider()
        
        # 🤖 LLM 智慧輔助決策控制台
        st.markdown("#### 🤖 智慧輔助決策")
        with st.container(border=True):
            st.markdown('<div class="ai-console-marker"></div>', unsafe_allow_html=True)
            st.markdown("##### 🧠 地端大腦建議 (Ollama)")
            ai_prompt = st.text_input("輸入對策諮詢問題", value="請評估當前資安告警並提供防範對策", key="ai_advice_prompt")
            if st.button("💡 向 AI 請求分析建議", use_container_width=True):
                if not ai_prompt:
                    st.warning("⚠️ 請輸入諮詢問題")
                else:
                    # [Agentic HITL] 每次發出新請求時，重置上一次的執行防呆旗標與結果
                    st.session_state["ai_recommended_action"] = None
                    st.session_state["ai_action_executed"]    = False
                    st.session_state["ai_action_result"]      = None

                    try:
                        headers = {"Authorization": f"Bearer {token}"}
                        # 1. 提交非同步任務請求
                        with st.spinner("🚀 正在送出 AI 決策請求..."):
                            r = requests.post(
                                f"{BACKEND}/api/ai/generate_advice",
                                json={"prompt": ai_prompt},
                                headers=headers,
                                timeout=15
                            )

                        if r.status_code == 200:
                            res_data = r.json()
                            task_id  = res_data.get("task_id")

                            # 2. 建立動態輪詢 placeholder
                            status_placeholder = st.empty()
                            finished    = False
                            max_retries = 60
                            retry_count = 0

                            while not finished and retry_count < max_retries:
                                # 查詢最新狀態
                                status_resp = requests.get(
                                    f"{BACKEND}/api/ai/task_status/{task_id}",
                                    headers=headers,
                                    timeout=5
                                )
                                if status_resp.status_code == 200:
                                    task_info  = status_resp.json()
                                    cur_status = task_info.get("status")

                                    if cur_status == "PENDING":
                                        status_placeholder.warning("⏳ 系統忙碌中，AI 正在排隊中...")
                                    elif cur_status == "RUNNING":
                                        status_placeholder.info("🤖 地端模型正在推理中...")
                                    elif cur_status == "SUCCESS":
                                        status_placeholder.empty()
                                        st.success("🟢 AI 建議分析完成！")
                                        st.markdown("**🤖 地端大腦建議：**")
                                        st.info(task_info.get("advice"))
                                        st.markdown(
                                            f'<div class="ai-latency-tag">⏱️ 耗時：{task_info.get("latency_ms")} ms</div>',
                                            unsafe_allow_html=True
                                        )
                                        # [Agentic HITL] 將 recommended_action 存入 session_state
                                        # Streamlit rerun 後會在下方渲染授權執行按鈕
                                        st.session_state["ai_recommended_action"] = task_info.get("recommended_action")
                                        finished = True
                                    elif cur_status == "FAILED":
                                        status_placeholder.empty()
                                        st.error(f"❌ AI 推理失敗：{task_info.get('error', '未知錯誤')}")
                                        finished = True
                                else:
                                    status_placeholder.error(f"⚠️ 查詢狀態異常 ({status_resp.status_code})")
                                    finished = True

                                if not finished:
                                    time.sleep(2)
                                    retry_count += 1

                            if not finished and retry_count >= max_retries:
                                status_placeholder.error("❌ 輪詢逾時，請稍後重試")

                        elif r.status_code == 403:
                            st.error("❌ 403 Forbidden: 權限不足，拒絕存取 AI 諮詢端點")
                        elif r.status_code == 400:
                            st.error(f"🛡️ 安全中樞攔截阻斷：{r.json().get('detail')}")
                        else:
                            st.error(f"⚠️ 後端伺服器異常 ({r.status_code})：{r.text}")
                    except Exception as e:
                        st.error(f"❌ 呼叫 AI 端點失敗：{e}")

            # ────────────────────────────────────────────────────────────────
            # [Agentic HITL] 授權執行按鈕渲染區
            # 此區塊跟「向 AI 請求分析建議」按鈕並列，在每次 Streamlit rerun 時重新渲染。
            # 串接邏輯：
            #   (A) 有 recommended_action 且尚未執行 → 顯示【⚡ 授權執行】按鈕
            #   (B) 已授權執行                       → 顯示執行成功詳細資訊
            #   (C) 無 recommended_action            → 不顯示任何額外元素
            # ────────────────────────────────────────────────────────────────
            rec_action  = st.session_state.get("ai_recommended_action")
            is_executed = st.session_state.get("ai_action_executed", False)

            # (A) 有建議動作且尚未執行 — 顯示授權按鈕
            if rec_action and not is_executed:
                display_name = rec_action.get("display_name") or rec_action.get("action_type", "未知動作")
                action_type  = rec_action.get("action_type", "")
                target       = rec_action.get("target", "未指定")
                reason       = rec_action.get("reason", "")

                # AI 建議執行動作說明卡（瑩光橙色卡）
                st.markdown(f"""
                <div style="
                    background: rgba(245,158,11,0.06);
                    border: 1px solid rgba(245,158,11,0.30);
                    border-radius: 8px;
                    padding: 12px 16px;
                    margin-top: 14px;
                ">
                    <div style="color:#F59E0B; font-size:0.78rem; font-weight:600;
                                letter-spacing:0.05em; text-transform:uppercase; margin-bottom:6px;">
                        ⚡ AI 建議執行動作
                    </div>
                    <div style="color:#FCD34D; font-size:1.05rem; font-weight:700; margin-bottom:4px;">
                        {display_name}
                    </div>
                    <div style="color:#94a3b8; font-size:0.82rem;">🎯 目標：{target}</div>
                    <div style="color:#64748b; font-size:0.80rem; margin-top:4px;">💬 {reason}</div>
                </div>
                """, unsafe_allow_html=True)

                # 【⚡ 授權 AI 執行】按鈕
                # 防呆機制：利用 session_state["ai_action_executed"] = True 在點擊瞬間阻斷重複請求
                if st.button(
                    f"⚡ 授權 AI 執行：{display_name}",
                    key="btn_authorize_action",
                    use_container_width=True,
                    type="primary"
                ):
                    # 防呆：先將旗標設為 True，避免使用者在 spinner 期間重複點擊
                    st.session_state["ai_action_executed"] = True

                    with st.spinner("🤖 AI 正在連線執行中..."):
                        try:
                            exec_resp = requests.post(
                                f"{BACKEND}/api/actions/execute",
                                json={
                                    "action_type": action_type,
                                    "payload": {
                                        "target":     target,
                                        "issue_type": rec_action.get("issue_type", ""),
                                        "department": rec_action.get("department", ""),
                                        "reason":     reason,
                                    }
                                },
                                headers={"Authorization": f"Bearer {token}"},
                                timeout=20
                            )

                            if exec_resp.status_code == 200:
                                # 執行成功，儲存結果至 session_state
                                st.session_state["ai_action_result"] = exec_resp.json()
                            else:
                                # 執行失敗：重置防呆旗標，讓使用者可重試
                                st.session_state["ai_action_executed"] = False
                                st.error(f"❌ 執行失敗 ({exec_resp.status_code})：{exec_resp.text}")
                        except Exception as ex:
                            st.session_state["ai_action_executed"] = False
                            st.error(f"❌ 連線後端執行 API 失敗：{ex}")

                    # 執行完成後重新渲染頁面，進入 (B) 狀態顯示成功結果
                    st.rerun()

            # (B) 已授權執行 — 顯示執行成功詳細資訊
            elif rec_action and is_executed:
                exec_data   = st.session_state.get("ai_action_result") or {}
                inner       = exec_data.get("result", {})
                result_text = inner.get("result", "執行完成") if inner else "執行完成"
                executed_at = inner.get("executed_at", "") if inner else ""

                # 執行成功——綠色微發光資訊卡
                st.markdown("""
                <div class="action-success-badge">
                    ✅ 動作已成功執行，並寫入系統稽核軌跡
                </div>""", unsafe_allow_html=True)

                if result_text:
                    st.markdown(f"""
                    <div class="action-detail-card">
                        <strong>📄 執行結果：</strong><br>{result_text}
                        {'<br><strong>⏰ 執行時間：</strong> ' + executed_at if executed_at else ''}
                    </div>""", unsafe_allow_html=True)

                st.caption("🔒 防呆：授權按鈕已失效。請重新發出 AI 諮詢以執行新動作。")




# ─── Tab 2：手動觸發稽核 ─────────────────────────────────────
with tab2:
    st.markdown("## 🚨 手動觸發 AI 合規稽核")
    st.info("💡 此介面模擬 Power BI Webhook 觸發情境，也可由排程系統自動呼叫後端 API。")

    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.markdown("### 📥 輸入異常數據")
        with st.container(border=True):
            carbon = st.slider(
                "碳排放強度（kgCO₂e/unit）",
                min_value=0.0, max_value=3.0, step=0.05,
                key="sim_carbon",
                help="ISO 14064-1 規定上限為 1.0"
            )

            # 動態顯示狀態
            if carbon <= 1.0:
                st.success(f"🟢 正常範圍（{carbon:.2f} ≤ 1.0）")
            elif carbon <= 1.5:
                st.warning(f"🟡 輕度超標（{carbon:.2f}，Level-1）")
            elif carbon <= 2.0:
                st.warning(f"🟠 嚴重超標（{carbon:.2f}，Level-2）")
            else:
                st.error(f"🔴 緊急超標（{carbon:.2f}，Level-3）")

            yield_rate = st.slider("當班良率（%）", 0.0, 100.0, step=0.1, key="sim_yield")
            user_id    = st.text_input("操作人員 ID", key="sim_user")
            department = st.selectbox("部門", ["製造一部", "製造二部", "品保部", "資安部"], key="sim_dept")
            shift      = st.selectbox("班別", ["A班", "B班", "C班"], key="sim_shift")
            equip_id   = st.text_input("設備編號", key="sim_equip")
            log_text   = st.text_area("資安事件日誌", key="sim_log", height=120)

    with col_right:
        st.markdown("### 🤖 AI 稽核執行")
        with st.container(border=True):
            st.markdown("**流程說明：**")
            st.markdown("""
            ```
            ① 接收數據（FastAPI Webhook）
                    ↓
            ② 資安去識別化（Anonymization）
                    ↓
            ③ 規則式風險評級（Rule Engine）
                    ↓
            ④ RAG 向量檢索（ChromaDB）
                    ↓
            ⑤ Prompt 工程組裝
                    ↓
            ⑥ 本地 AI 推理（Qwen 2.5:14b）
                    ↓
            ⑦ CAPA 報告生成 ✅
            ```
            """)

            if st.button("🚨 立即觸發 AI 稽核", type="primary", use_container_width=True):
                payload = {
                    "carbon_intensity":  carbon,
                    "user_id":           user_id,
                    "event_log":         log_text,
                    "department":        department,
                    "shift":             shift,
                    "equipment_id":      equip_id,
                    "production_yield":  yield_rate
                }

                with st.spinner("📡 正在發送至後端 API..."):
                    result = api_post("/api/v1/trigger_audit", payload)

                if result and "task_id" in result:
                    task_id = result["task_id"]
                    # [FEATURE] HITL 審核機制：統一將手動觸發任務重導向至頁面頂部的狀態顯示區以維持狀態
                    st.session_state["demo_task_id"] = task_id
                    st.session_state["demo_status"] = "polling"
                    st.session_state["demo_report"] = None
                    st.toast("✅ 任務已接收，開始非同步稽核！", icon="📡")
                    st.rerun()
                else:
                    st.error(f"❌ API 呼叫失敗：{result}")

            # 快速風險預評（同步）
            if st.button("⚡ 快速風險預評（即時）", use_container_width=True):
                payload = {
                    "carbon_intensity":  carbon,
                    "user_id":           user_id,
                    "event_log":         log_text,
                    "production_yield":  yield_rate
                }
                result = api_post("/api/v1/quick_risk", payload)
                if result and "risk" in result:
                    risk = result["risk"]
                    level = risk.get("risk_level", 1)
                    st.markdown(f"### {risk.get('risk_label')}")
                    for r in risk.get("reasons", []):
                        st.warning(r)
                    st.info(f"⏱️ 回應時限：{risk.get('response_time')}")

        st.markdown("### ⚙️ 系統模擬控制中心")
        with st.container(border=True):
            st.markdown("**1. 快速載入情境範本：**")
            col_ehs, col_mes, col_siem = st.columns(3)
            
            col_ehs.button("🔋 載入 EHS 異常", use_container_width=True, on_click=load_ehs_scenario)
            col_mes.button("⚙️ 載入 MES 異常", use_container_width=True, on_click=load_mes_scenario)
            col_siem.button("🛡️ 載入 SIEM 異常", use_container_width=True, on_click=load_siem_scenario)
            
            st.divider()
            st.markdown("**2. 全自動隨機轟擊：**")
            
            # 使用 st.session_state 狀態來做開關
            auto_btn = st.toggle("🚀 開啟全自動隨機轟擊 (每 5 分鐘自動模擬發送)", value=st.session_state["sim_active"])
            if auto_btn != st.session_state["sim_active"]:
                st.session_state["sim_active"] = auto_btn
                if auto_btn:
                    stop_event = threading.Event()
                    thread = threading.Thread(target=bombard_worker, args=(stop_event,), daemon=True)
                    thread.start()
                    st.session_state["sim_thread"] = thread
                    st.session_state["sim_stop_event"] = stop_event
                    st.success("背景隨機轟擊已啟動！系統正每 5 分鐘向後端發送一筆隨機異常。")
                else:
                    if st.session_state["sim_stop_event"] is not None:
                        st.session_state["sim_stop_event"].set()
                    st.session_state["sim_thread"] = None
                    st.session_state["sim_stop_event"] = None
                    st.info("已停止自動隨機轟擊模式。")
                st.rerun()
                
            if st.session_state["sim_active"]:
                # 雙重檢查執行緒是否還活著，避免意外中止
                t = st.session_state["sim_thread"]
                if t is None or not t.is_alive():
                    stop_event = threading.Event()
                    thread = threading.Thread(target=bombard_worker, args=(stop_event,), daemon=True)
                    thread.start()
                    st.session_state["sim_thread"] = thread
                    st.session_state["sim_stop_event"] = stop_event
                st.info("🟢 自動轟擊中：背景執行緒正在每 5 分鐘隨機打擊 API 接口。")


# ─── Tab 3：歷史報告查閱 ─────────────────────────────────────
with tab3:
    st.markdown("## 📋 歷史稽核報告")

    col_refresh, col_filter = st.columns([1, 3])
    with col_refresh:
        if st.button("🔄 刷新列表"):
            st.rerun()

    reports = api_get("/api/v1/reports")

    if reports:
        # [Step 4] 支援 risk_label 欄位（舊 API 是 risk_level 字串欄位名稱不一致，統一修正）
        for r in reports:
            if "risk_label" not in r and "risk_level" in r:
                lv = r.get("risk_level", 1)
                r["risk_label"] = {1: "Level-1 輕微", 2: "Level-2 嚴重", 3: "Level-3 緊急"}.get(lv, str(lv))
        df = pd.DataFrame(reports)
        # 保留有意義的欄位
        display_cols = [c for c in ["task_id", "status", "created_at", "risk_label", "department", "shift"] if c in df.columns]
        st.dataframe(df[display_cols], use_container_width=True, hide_index=True)

        st.markdown("---")
        task_ids = [r["task_id"] for r in reports]
        selected = st.selectbox("選擇 Task ID 查看詳細報告", task_ids)

        if selected:
            detail = api_get(f"/api/v1/report/{selected}")
            if detail:
                # 取得資料
                risk = detail.get("risk_assessment", {})
                risk_lv = risk.get("risk_level", 1)
                risk_lbl = risk.get("risk_label", "Level-1 輕微")
                reasons = risk.get("reasons", [])
                resp_time = risk.get("response_time", "")
                
                # [DEMO FEATURE] 1. [AI 診斷結果]
                st.markdown("### 📊 [AI 診斷結果]")
                
                # 依風險等級顯示不同顏色的 Alert
                if risk_lv == 3:
                    st.error(f"**風險級別：🔴 {risk_lbl}**")
                elif risk_lv == 2:
                    st.warning(f"**風險級別：🟠 {risk_lbl}**")
                else:
                    st.success(f"**風險級別：🟢 {risk_lbl}**")
                
                # 顯示原因清單與時限
                col_info1, col_info2 = st.columns([2, 1])
                with col_info1:
                    st.markdown("**判定原因：**")
                    for r in reasons:
                        st.markdown(f"- ⚠️ {r}")
                with col_info2:
                    st.markdown("**要求回應時限：**")
                    st.info(f"⏱️ {resp_time}")
                
                # 2. 顯示去識別化數據
                st.markdown("---")
                st.subheader("🔒 去識別化稽核數據 (已完成隱私防護)")
                
                anon = detail.get("anonymized_data", {})
                if anon:
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("去識別化操作員", anon.get("user_id", "N/A"))
                    c2.metric("部門 / 班別", f"{anon.get('department', 'N/A')} / {anon.get('shift', 'N/A')}")
                    c3.metric("碳排放強度 (kgCO₂e)", f"{anon.get('carbon_intensity', 0.0):.2f}")
                    c4.metric("當班生產良率", f"{anon.get('yield_rate', 0.0):.1f}%" if anon.get('yield_rate') is not None else "N/A")
                    
                    st.markdown("**去識別化事件日誌：**")
                    st.code(anon.get("event_log", "N/A"), language="text")
                
                # [DEMO FEATURE] 3. [Agent 執行動作]
                # [FEATURE] HITL 審核機制：支援待審核與退回狀態之 Agent 行動說明
                st.markdown("---")
                st.markdown("### 🤖 [Agent 執行動作]")
                agent_action = detail.get("agent_notification")
                if not agent_action and detail.get("status") == "pending_approval":
                    agent_action = f"[待審批] 預計執行行動：{detail.get('proposed_action', '無')}"
                elif not agent_action and detail.get("status") == "rejected":
                    agent_action = f"[已退回] 由 {detail.get('rejected_by')} 退回，原因：{detail.get('reject_reason')}"
                
                if agent_action:
                    st.info(agent_action)
                else:
                    st.info("無觸發任何 Agent 模擬防禦或通報動作。")

                # [DEMO FEATURE] 4. [生成之 CAPA 報告]
                if detail.get("ai_capa_report"):
                    st.markdown("---")
                    st.markdown("### 📄 [生成之 CAPA 報告]")
                    st.markdown(
                        f'<div class="report-box">{detail["ai_capa_report"]}</div>',
                        unsafe_allow_html=True
                    )
                    
                    # 下載按鈕
                    st.download_button(
                        "📥 下載報告（JSON）",
                        data=json.dumps(detail, ensure_ascii=False, indent=2),
                        file_name=f"capa_report_{selected}.json",
                        mime="application/json"
                    )

                    # [FEATURE] 匯出正式報告功能
                    if detail.get("status") == "completed":
                        try:
                            headers = {}
                            if "token" in st.session_state and st.session_state["token"]:
                                headers["Authorization"] = f"Bearer {st.session_state['token']}"
                            res = requests.get(f"{BACKEND}/api/task/{selected}/export", headers=headers, timeout=5)
                            if res.status_code == 200:
                                st.download_button(
                                    label="📥 下載官方 ISO 改善對策報告 (Word)",
                                    data=res.content,
                                    file_name=f"ISO_Audit_Report_{selected}.docx",
                                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                    key=f"btn_export_history_{selected}"
                                )
                        except Exception as e:
                            st.error(f"⚠️ 無法下載 Word 報告：{e}")
    else:
        st.info("📭 尚無稽核報告，請至「手動觸發稽核」頁籤觸發第一筆稽核")


# ─── Tab 4：系統架構說明 ─────────────────────────────────────
with tab4:
    st.markdown("## 🧠 系統架構說明")

    st.markdown("""
    ### 完整資料流

    ```
    ┌──────────────────────────────────────────────────────────┐
    │                  輸入層（Data Sources）                   │
    │   Power BI Webhook  ·  MES 系統  ·  手動觸發              │
    └──────────────────┬───────────────────────────────────────┘
                       │ HTTP POST（異常數據）
    ┌──────────────────▼───────────────────────────────────────┐
    │              FastAPI 後端（Port 8000）                    │
    │  ① 去識別化（Anonymization）                              │
    │  ② 規則式風險評級（Rule Engine）                          │
    │  ③ RAG 向量檢索（ChromaDB Port 本地）                    │
    │  ④ Prompt 組裝 → 呼叫 Ollama（Port 11434）               │
    └──────────────────┬───────────────────────────────────────┘
                       │ 非同步回傳
    ┌──────────────────▼───────────────────────────────────────┐
    │           Streamlit 前端（Port 8501）                     │
    │   Dashboard · 觸發介面 · CAPA 報告閱覽                   │
    └──────────────────────────────────────────────────────────┘
    ```

    ### 安全設計原則
    - 🔒 所有 PII 資料在進入 AI 前完成去識別化
    - 🏠 LLM 完全運行於本地，零數據外洩風險
    - 📋 ISO 知識庫本地向量化，不依賴任何 SaaS
    - 🔐 GCP 憑證透過 Secret Manager 管理

    ### 技術棧
    | 層級 | 技術 | 用途 |
    |------|------|------|
    | 前端 | Streamlit | Dashboard + 互動介面 |
    | 後端 | FastAPI | Webhook + 去識別化 + 路由 |
    | 向量庫 | ChromaDB | ISO 條文 RAG 檢索 |
    | LLM | Qwen 2.5:14b @ Ollama | CAPA 報告生成 |
    | 嵌入 | nomic-embed-text | 向量化 |
    | 部署 | GCP Cloud Run + GitHub Actions | CI/CD |
    """)
