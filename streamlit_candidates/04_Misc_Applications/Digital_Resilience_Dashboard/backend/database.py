import streamlit as st
st.title('database.py - 自動化展示')
st.info('這是從原專案腳本自動包裝產生的互動式介面。')

"""
database.py — SQLite 資料庫管理模組
功能：
  1. audit_logs  — 操作與 AI 生成稽核日誌（Step 2）
  2. reports     — 完整稽核任務報告持久化（Step 4）
"""
import sqlite3
import json
import os
from datetime import datetime
from typing import Optional, List, Dict, Any

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "audit.db")


def init_db():
    """初始化 SQLite 資料庫，建立 audit_logs 與 reports 資料表"""
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    cursor = conn.cursor()

    # ── 資料表 1：操作稽核日誌 ─────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp     TEXT NOT NULL,
            username      TEXT NOT NULL,
            role          TEXT NOT NULL,
            action_type   TEXT NOT NULL,
            action_details TEXT NOT NULL,
            prompt        TEXT,
            ai_response   TEXT,
            latency_ms    INTEGER
        )
    """)

    # ── 資料表 2：完整稽核任務報告（Step 4 新增）──────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            task_id     TEXT PRIMARY KEY,
            status      TEXT NOT NULL,
            created_at  TEXT NOT NULL,
            updated_at  TEXT NOT NULL,
            risk_level  INTEGER DEFAULT 1,
            risk_label  TEXT DEFAULT 'Level-1 輕微',
            department  TEXT,
            shift       TEXT,
            data_json   TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


# ══════════════════════════════════════════════════════════════
#  audit_logs CRUD
# ══════════════════════════════════════════════════════════════

def log_audit_event(username: str, role: str, action_type: str, action_details: str,
                    prompt: Optional[str] = None, ai_response: Optional[str] = None,
                    latency_ms: Optional[int] = None):
    """寫入審計與操作日誌事件"""
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    cursor = conn.cursor()
    timestamp = datetime.now().isoformat()
    cursor.execute("""
        INSERT INTO audit_logs (timestamp, username, role, action_type, action_details, prompt, ai_response, latency_ms)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (timestamp, username, role, action_type, action_details, prompt, ai_response, latency_ms))
    conn.commit()
    conn.close()


def get_audit_logs(limit: int = 50) -> List[Dict[str, Any]]:
    """獲取最新 N 筆審計日誌"""
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, timestamp, username, role, action_type, action_details, prompt, ai_response, latency_ms
        FROM audit_logs
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))
    conn.close()
    return [dict(row) for row in rows]


def get_audit_logs_since(days: int = 7) -> List[Dict[str, Any]]:
    """獲取指定天數以內的審計日誌 (Step 5)"""
    from datetime import datetime, timedelta
    since_time = (datetime.now() - timedelta(days=days)).isoformat()
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, timestamp, username, role, action_type, action_details, prompt, ai_response, latency_ms
        FROM audit_logs
        WHERE timestamp >= ?
        ORDER BY id DESC
    """, (since_time,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


# ══════════════════════════════════════════════════════════════
#  reports CRUD（Step 4 新增）
# ══════════════════════════════════════════════════════════════

def save_report(task_id: str, data_dict: dict):
    """
    儲存或更新一筆稽核報告至 SQLite。
    data_dict 為完整的 report_store[task_id] 字典，以 JSON 形式儲存於 data_json 欄位。
    快速查詢欄位（status, risk_level 等）另外獨立儲存以供列表查詢使用。
    """
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    cursor = conn.cursor()

    status     = data_dict.get("status", "processing")
    created_at = data_dict.get("created_at", datetime.now().isoformat())
    updated_at = datetime.now().isoformat()

    risk = data_dict.get("risk_assessment", {})
    risk_level = risk.get("risk_level", 1)
    risk_label = risk.get("risk_label", "Level-1 輕微")

    input_data = data_dict.get("input", {})
    anon_data  = data_dict.get("anonymized_data", {})
    department = anon_data.get("department") or input_data.get("department", "")
    shift      = anon_data.get("shift") or input_data.get("shift", "")

    data_json = json.dumps(data_dict, ensure_ascii=False)

    cursor.execute("""
        INSERT INTO reports (task_id, status, created_at, updated_at, risk_level, risk_label, department, shift, data_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(task_id) DO UPDATE SET
            status     = excluded.status,
            updated_at = excluded.updated_at,
            risk_level = excluded.risk_level,
            risk_label = excluded.risk_label,
            department = excluded.department,
            shift      = excluded.shift,
            data_json  = excluded.data_json
    """, (task_id, status, created_at, updated_at, risk_level, risk_label, department, shift, data_json))

    conn.commit()
    conn.close()


def get_report(task_id: str) -> Optional[Dict[str, Any]]:
    """依 task_id 讀取完整報告；不存在則回傳 None"""
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT data_json FROM reports WHERE task_id = ?", (task_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return json.loads(row["data_json"])
    return None


def list_reports(limit: int = 100) -> List[Dict[str, Any]]:
    """
    列出報告摘要（輕量版，不含 AI 全文）。
    回傳欄位：task_id, status, created_at, updated_at, risk_level, risk_label, department, shift
    """
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT task_id, status, created_at, updated_at, risk_level, risk_label, department, shift
        FROM reports
        ORDER BY created_at DESC
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_reports_for_recovery(limit: int = 50) -> List[Dict[str, Any]]:
    """
    供啟動恢復機制使用：讀取最近 N 筆 pending_approval 或 processing 狀態的完整報告。
    """
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT data_json FROM reports
        WHERE status IN ('pending_approval', 'processing')
        ORDER BY created_at DESC
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [json.loads(row["data_json"]) for row in rows]


def get_db_stats() -> Dict[str, Any]:
    """回傳資料庫統計摘要，供健康檢查使用"""
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM audit_logs")
    audit_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM reports")
    report_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM reports WHERE status = 'completed'")
    completed_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM reports WHERE status = 'pending_approval'")
    pending_count = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) FROM reports
        WHERE date(created_at) = date('now', 'localtime')
    """)
    today_count = cursor.fetchone()[0]

    conn.close()
    return {
        "audit_log_count":    audit_count,
        "total_reports":      report_count,
        "completed_reports":  completed_count,
        "pending_approval":   pending_count,
        "today_reports":      today_count,
    }


# ====== 自動生成的測試執行區塊 ======
if __name__ == "__main__":
    st.write("---")
    st.subheader("函數測試區塊")
    if st.button("執行 init_db"):
        try:
            res = init_db() # 請視需要自行補上參數
            st.write("執行結果:", res)
        except Exception as e:
            st.error(f"執行出錯，可能需要提供參數：{e}")
    if st.button("執行 log_audit_event"):
        try:
            res = log_audit_event() # 請視需要自行補上參數
            st.write("執行結果:", res)
        except Exception as e:
            st.error(f"執行出錯，可能需要提供參數：{e}")
    if st.button("執行 get_audit_logs"):
        try:
            res = get_audit_logs() # 請視需要自行補上參數
            st.write("執行結果:", res)
        except Exception as e:
            st.error(f"執行出錯，可能需要提供參數：{e}")
    if st.button("執行 get_audit_logs_since"):
        try:
            res = get_audit_logs_since() # 請視需要自行補上參數
            st.write("執行結果:", res)
        except Exception as e:
            st.error(f"執行出錯，可能需要提供參數：{e}")
    if st.button("執行 save_report"):
        try:
            res = save_report() # 請視需要自行補上參數
            st.write("執行結果:", res)
        except Exception as e:
            st.error(f"執行出錯，可能需要提供參數：{e}")
    if st.button("執行 get_report"):
        try:
            res = get_report() # 請視需要自行補上參數
            st.write("執行結果:", res)
        except Exception as e:
            st.error(f"執行出錯，可能需要提供參數：{e}")
    if st.button("執行 list_reports"):
        try:
            res = list_reports() # 請視需要自行補上參數
            st.write("執行結果:", res)
        except Exception as e:
            st.error(f"執行出錯，可能需要提供參數：{e}")
    if st.button("執行 get_reports_for_recovery"):
        try:
            res = get_reports_for_recovery() # 請視需要自行補上參數
            st.write("執行結果:", res)
        except Exception as e:
            st.error(f"執行出錯，可能需要提供參數：{e}")
    if st.button("執行 get_db_stats"):
        try:
            res = get_db_stats() # 請視需要自行補上參數
            st.write("執行結果:", res)
        except Exception as e:
            st.error(f"執行出錯，可能需要提供參數：{e}")
