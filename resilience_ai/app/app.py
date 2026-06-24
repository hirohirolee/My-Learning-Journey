"""
app.py — 企業數位韌性 AI 導航系統（Streamlit 前端）
功能：即時數據監控 Dashboard + 手動/自動稽核觸發 + CAPA 報告閱覽
"""

import time
import json
import requests
import pandas as pd
import streamlit as st
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

# 全局模擬狀態控管
if "global_sim_state" not in globals():
    globals()["global_sim_state"] = {"active": False, "thread": None}

def bombard_worker():
    import requests
    import time
    import random
    
    api_url = "http://localhost:8000/api/v1/trigger_audit"
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
    
    sim_state = globals()["global_sim_state"]
    while sim_state["active"]:
        try:
            scenario = random.choice(scenarios).copy()
            if scenario["user_id"] == "EHS_Monitor":
                scenario["carbon_intensity"] = round(random.uniform(1.2, 2.5), 2)
            elif scenario["user_id"] == "生管主管":
                scenario["production_yield"] = round(random.uniform(65.0, 84.0), 1)
            requests.post(api_url, json=scenario, timeout=3)
        except Exception:
            pass
        time.sleep(180)  # 改為 3 分鐘 (180 秒)，避免後端因太頻繁啟動 AI 推理而阻塞

# ── 頁面基本設定 ─────────────────────────────────────────────
st.set_page_config(
    page_title="企業數位韌性 AI 導航系統",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

BACKEND = "http://localhost:8000"

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
                    st.success(f"✅ 任務已接收！Task ID：`{task_id}`")
                    st.session_state["last_task_id"] = task_id

                    # 等待並輪詢結果
                    st.markdown("---")
                    st.markdown("**⏳ 等待 AI 推理中...**")
                    progress = st.progress(0, "初始化中...")

                    for i in range(30):
                        time.sleep(2)
                        progress.progress((i + 1) / 30, f"AI 分析中... ({(i+1)*2}秒)")
                        report = api_get(f"/api/v1/report/{task_id}")
                        if report and report.get("status") in ("completed", "failed"):
                            progress.progress(1.0, "完成！")
                            break

                    if report and report.get("status") == "completed":
                        risk = report.get("risk_assessment", {})
                        st.error(f"🚨 風險等級：{risk.get('risk_label', 'N/A')}")
                        for reason in risk.get("reasons", []):
                            st.warning(f"⚠️ {reason}")

                        st.markdown("### 📄 AI 生成 CAPA 報告")
                        st.markdown(
                            f'<div class="report-box">{report.get("ai_capa_report", "")}</div>',
                            unsafe_allow_html=True
                        )
                    elif report and report.get("status") == "failed":
                        st.error(f"❌ 稽核失敗：{report.get('error')}")
                    else:
                        st.info("⏳ AI 仍在推理中，請至「歷史報告」頁籤查詢結果")
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
            
            sim_state = globals()["global_sim_state"]
            import threading
            
            auto_btn = st.toggle("🚀 開啟全自動隨機轟擊 (每 3 秒自動模擬發送)", value=sim_state["active"])
            if auto_btn != sim_state["active"]:
                sim_state["active"] = auto_btn
                if auto_btn:
                    if sim_state["thread"] is None or not sim_state["thread"].is_alive():
                        sim_state["thread"] = threading.Thread(target=bombard_worker, daemon=True)
                        sim_state["thread"].start()
                    st.success("背景隨機轟擊已啟動！系統正每 3 秒向後端發送一筆隨機異常。")
                else:
                    st.info("已停止自動隨機轟擊模式。")
                st.rerun()
                
            if sim_state["active"]:
                st.info("🟢 自動轟擊中：背景執行緒正在每 3 秒隨機打擊 API 接口。")


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
                st.json(detail.get("risk_assessment", {}))
                if detail.get("ai_capa_report"):
                    st.markdown("### 📄 CAPA 報告全文")
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
