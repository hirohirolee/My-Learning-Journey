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
    /* 主色調 */
    :root {
        --primary:   #1e40af;
        --warning:   #d97706;
        --danger:    #dc2626;
        --success:   #16a34a;
        --surface:   #1e293b;
    }

    /* 卡片樣式 */
    .metric-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        color: white;
    }
    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        margin: 8px 0;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* 狀態標籤 */
    .badge-safe     { background:#16a34a20; color:#16a34a; padding:4px 12px; border-radius:20px; font-size:0.8rem; border:1px solid #16a34a40; }
    .badge-warn     { background:#d9770620; color:#d97706; padding:4px 12px; border-radius:20px; font-size:0.8rem; border:1px solid #d9770640; }
    .badge-critical { background:#dc262620; color:#dc2626; padding:4px 12px; border-radius:20px; font-size:0.8rem; border:1px solid #dc262640; }

    /* 報告區塊 */
    .report-box {
        background: #0f172a;
        border: 1px solid #1e40af;
        border-radius: 8px;
        padding: 20px;
        color: #e2e8f0;
        font-family: 'Noto Sans TC', monospace;
        line-height: 1.8;
        white-space: pre-wrap;
    }

    /* 隱藏 Streamlit 預設元素 */
    #MainMenu { visibility: hidden; }
    footer    { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ╔══════════════════════════════════════════════════════════╗
# ║  工具函式                                                ║
# ╚══════════════════════════════════════════════════════════╝

def api_get(path: str) -> dict | None:
    try:
        r = requests.get(f"{BACKEND}{path}", timeout=1)  # 縮短為 1 秒超時，防止後端忙碌時卡住前端網頁畫面
        return r.json()
    except Exception:
        return None

def api_post(path: str, data: dict) -> dict | None:
    try:
        r = requests.post(f"{BACKEND}{path}", json=data, timeout=10)
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

with st.sidebar:
    st.markdown("## 🛡️ 系統控制台")
    st.divider()

    # 系統狀態
    health = api_get("/health")
    if health:
        st.markdown("### 📡 子系統狀態")
        for key, val in health.items():
            if key == "active_tasks":
                st.metric("進行中稽核", val)
                continue
            color = "🟢" if "online" in str(val) else "🔴"
            st.markdown(f"{color} **{key.upper()}**: `{val}`")
    else:
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
    st.caption(f"🕐 最後更新：{datetime.now().strftime('%H:%M:%S')}")
    st.caption("© 2025 企業數位韌性系統 v2.0")


# ╔══════════════════════════════════════════════════════════╗
# ║  主頁面                                                  ║
# ╚══════════════════════════════════════════════════════════╝

st.markdown("# 🛡️ 企業數位韌性 AI 導航系統")
st.markdown("**地端安全私有化 AI 決策中樞** ｜ ISO 14064-1 × ISO 27001 × 生管 SOP 三合一合規稽核")
st.divider()

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
                    res = requests.get(f"{BACKEND}/api/task/{export_task_id}/export", timeout=5)
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

    # 模擬即時數據
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-label">碳排放強度</div>
            <div class="metric-value" style="color:#d97706">1.45</div>
            <div class="metric-label">kgCO₂e/unit ⚠️ 超標</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-label">當班良率</div>
            <div class="metric-value" style="color:#dc2626">79.3%</div>
            <div class="metric-label">目標 85% 🔴 未達標</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-label">資安事件</div>
            <div class="metric-value" style="color:#dc2626">2</div>
            <div class="metric-label">過去 24 小時 🔴</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-label">AI 稽核任務</div>
            <div class="metric-value" style="color:#16a34a">7</div>
            <div class="metric-label">今日完成 🟢</div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # 模擬趨勢圖表
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("### 碳排放強度趨勢（過去 8 班）")
        carbon_data = pd.DataFrame({
            "班別":   ["A班-1", "B班-1", "C班-1", "A班-2", "B班-2", "C班-2", "A班-3", "B班-3"],
            "碳強度": [0.92, 1.05, 0.88, 1.23, 1.45, 1.31, 1.67, 1.45],
            "上限":   [1.0] * 8
        })
        st.line_chart(carbon_data.set_index("班別")[["碳強度", "上限"]])

    with col_b:
        st.markdown("### 良率趨勢（過去 8 班）")
        yield_data = pd.DataFrame({
            "班別": ["A班-1", "B班-1", "C班-1", "A班-2", "B班-2", "C班-2", "A班-3", "B班-3"],
            "良率": [91.2, 88.5, 92.0, 85.3, 82.1, 79.3, 81.0, 79.3],
            "目標": [85.0] * 8
        })
        st.line_chart(yield_data.set_index("班別")[["良率", "目標"]])

    st.divider()
    st.markdown("### 🚨 近期告警事件")
    alerts = [
        {"時間": "03:42", "類型": "資安", "嚴重度": "🔴 Level-3", "說明": "深夜大量下載合規清冊（ISO 27001 A.8.16）"},
        {"時間": "06:15", "類型": "碳排放", "嚴重度": "🟠 Level-2", "說明": "碳強度 1.67 超標（上限 1.0）"},
        {"時間": "08:30", "類型": "生產", "嚴重度": "🟡 Level-2", "說明": "良率 79.3% 低於目標 85%"},
    ]
    st.dataframe(pd.DataFrame(alerts), use_container_width=True, hide_index=True)


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
        df = pd.DataFrame(reports)
        st.dataframe(df, use_container_width=True, hide_index=True)

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
                            res = requests.get(f"{BACKEND}/api/task/{selected}/export", timeout=5)
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
