import streamlit as st

"""
action_service.py — Agentic 自動化執行模組
============================================
功能：提供可由使用者授權執行的模擬自動化動作 (Agentic Actions)。
      每個動作皆模擬企業系統中的實際處置流程：
        - CREATE_CAPA      : 在 MES 建立 CAPA 矯正單
        - BLOCK_IP         : 在防火牆規則中封鎖異常 IP
        - NOTIFY_SUPPLIER  : 發送供應商異常通知 Email

設計原則 (Human-in-the-Loop):
  AI 提出建議 → 使用者在前端點擊授權 → 呼叫本模組執行 → 寫入稽核軌跡
  任何動作執行前皆須通過 Guardrails 防呆驗證，確保 payload 不含未遮蔽個資。

串接方式:
  main.py (POST /api/actions/execute)
    └─ call execute_action(action_type, payload)
        ├─ 驗證 payload 安全性 (Guardrails)
        ├─ asyncio.sleep 模擬處理時間
        └─ 回傳 ExecutionResult 字典
"""

import asyncio
import re
import logging
from datetime import datetime
from typing import Any

log = logging.getLogger(__name__)


# ── 支援的動作類型常數 ────────────────────────────────────────
ACTION_CREATE_CAPA       = "CREATE_CAPA"
ACTION_BLOCK_IP          = "BLOCK_IP"
ACTION_NOTIFY_SUPPLIER   = "NOTIFY_SUPPLIER"

# 合法的動作類型清單（防呆白名單）
VALID_ACTION_TYPES = {ACTION_CREATE_CAPA, ACTION_BLOCK_IP, ACTION_NOTIFY_SUPPLIER}

# 動作對應的繁體中文顯示名稱（供前端展示使用）
ACTION_DISPLAY_NAMES = {
    ACTION_CREATE_CAPA:     "建立 CAPA 矯正單 (MES)",
    ACTION_BLOCK_IP:        "封鎖異常 IP (防火牆)",
    ACTION_NOTIFY_SUPPLIER: "發送供應商異常通知 (Email)",
}

# 個資 PII 高風險正則表達式（用於執行前防呆驗證）
# 驗證 payload 中不含未遮蔽的身分證字號、Email、台灣手機號碼
_PII_PATTERNS = [
    r"\b[A-Z][12]\d{8}\b",                                 # 身分證字號
    r"[\w\.-]+@[\w\.-]+\.\w+",                              # Email
    r"\b09\d{2}-\d{3}-\d{3}\b|\b09\d{8}\b",               # 台灣手機號碼
]


def _validate_payload_no_pii(payload: dict) -> tuple[bool, str]:
    """
    Guardrails 防呆函式：掃描 payload 的所有字串值，
    確認不含未遮蔽的個資 (PII)。
    回傳: (is_safe: bool, reason: str)
    """
    payload_str = str(payload)
    for pattern in _PII_PATTERNS:
        if re.search(pattern, payload_str):
            return False, f"Payload 中偵測到未遮蔽的個人資料 (PII)，已阻斷執行以符合資料保護規範。"
    return True, ""


async def _simulate_create_capa(payload: dict) -> dict:
    """
    模擬情境一：在 MES (製造執行系統) 中建立 CAPA 矯正單
    ──────────────────────────────────────────────────────
    實際場景：呼叫 MES API 建立矯正預防單，指派給品保工程師，
              並設定完成期限與責任人層級。
    模擬處理時間：1.5 秒（模擬 MES API 網路延遲與資料庫寫入）
    """
    target      = payload.get("target", "未指定產線")
    department  = payload.get("department", "品保部")
    triggered_by = payload.get("triggered_by", "AI_System")

    log.info(f"[ACTION] CREATE_CAPA 開始執行 — 目標: {target}")

    # 模擬 MES API 呼叫的處理時間
    await asyncio.sleep(1.5)

    capa_id = f"CAPA-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    log.info(f"[ACTION] CREATE_CAPA 完成 — CAPA ID: {capa_id}")
    return {
        "status":       "success",
        "action_type":  ACTION_CREATE_CAPA,
        "capa_id":      capa_id,
        "target":       target,
        "department":   department,
        "assigned_to":  "品保工程師 (QE)",
        "due_within":   "24 小時",
        "triggered_by": triggered_by,
        "result":       f"CAPA 矯正單 [{capa_id}] 已成功建立於 MES 系統，指派給 {department} 品保工程師，要求 24 小時內完成根因分析。",
        "executed_at":  datetime.now().isoformat(),
    }


async def _simulate_block_ip(payload: dict) -> dict:
    """
    模擬情境二：在防火牆規則中封鎖異常來源 IP
    ──────────────────────────────────────────────────────
    實際場景：呼叫防火牆管理 API，新增 DROP 規則，封鎖來源 IP 的
              所有入站連線，並通知 CISO 與 SOC 團隊。
    模擬處理時間：2.0 秒（模擬防火牆 ACL 規則下推與同步）
    注意：IP 位址在傳入 payload 前已由 Guardrails 去識別化為 [IP_REMOVED]；
          此函式僅接收 target（可為去識別化後的標識符）。
    """
    target       = payload.get("target", "[IP_REMOVED]")
    triggered_by = payload.get("triggered_by", "AI_System")

    log.info(f"[ACTION] BLOCK_IP 開始執行 — 目標識別符: {target}")

    # 模擬防火牆規則下推的處理時間
    await asyncio.sleep(2.0)

    rule_id = f"FW-RULE-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    log.info(f"[ACTION] BLOCK_IP 完成 — 規則 ID: {rule_id}")
    return {
        "status":       "success",
        "action_type":  ACTION_BLOCK_IP,
        "rule_id":      rule_id,
        "target":       target,
        "rule_action":  "DROP",
        "scope":        "所有入站流量 (Inbound All)",
        "notified":     "CISO + SOC 團隊",
        "triggered_by": triggered_by,
        "result":       f"防火牆規則 [{rule_id}] 已成功建立，對目標 [{target}] 的所有入站連線已封鎖。CISO 與 SOC 已收到自動告警通知。",
        "executed_at":  datetime.now().isoformat(),
    }


async def _simulate_notify_supplier(payload: dict) -> dict:
    """
    模擬情境三：發送供應商異常通知 Email
    ──────────────────────────────────────────────────────
    實際場景：透過 ERP 的 Email 通知模組，將 ESG 碳排或交期異常
              情況自動通報給對應供應商窗口，並附帶矯正要求期限。
    模擬處理時間：1.0 秒（模擬 SMTP 發送與 ERP 日誌記錄）
    """
    target       = payload.get("target", "供應商 (未指定)")
    issue_type   = payload.get("issue_type", "ESG 碳排放異常")
    triggered_by = payload.get("triggered_by", "AI_System")

    log.info(f"[ACTION] NOTIFY_SUPPLIER 開始執行 — 對象: {target}, 事由: {issue_type}")

    # 模擬 SMTP 發送的處理時間
    await asyncio.sleep(1.0)

    ticket_id = f"SUP-TICKET-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    log.info(f"[ACTION] NOTIFY_SUPPLIER 完成 — 工單 ID: {ticket_id}")
    return {
        "status":       "success",
        "action_type":  ACTION_NOTIFY_SUPPLIER,
        "ticket_id":    ticket_id,
        "recipient":    target,
        "issue_type":   issue_type,
        "response_due": "72 小時",
        "triggered_by": triggered_by,
        "result":       f"供應商異常通知 [{ticket_id}] 已成功發送至 [{target}]，事由：{issue_type}。要求供應商於 72 小時內回覆矯正計畫。",
        "executed_at":  datetime.now().isoformat(),
    }


# ── 主要執行入口 ──────────────────────────────────────────────

async def execute_action(action_type: str, payload: dict) -> dict:
    """
    Agentic Action 主要執行函式
    ─────────────────────────────────────────────────────────────
    功能：
      1. 驗證 action_type 是否在合法白名單內（防止未知動作被執行）
      2. 執行 Guardrails PII 防呆驗證（確保 payload 不含敏感個資）
      3. 依據 action_type 分派至對應的模擬執行函式
      4. 回傳統一格式的 ExecutionResult 字典

    Args:
        action_type (str): 要執行的動作類型，必須是 VALID_ACTION_TYPES 之一
        payload (dict):    傳遞給動作執行函式的參數，
                           例如 {"target": "SMT-Line-03", "triggered_by": "admin"}

    Returns:
        dict: 包含 status, action_type, result, executed_at 等欄位的執行結果

    Raises:
        ValueError: action_type 不在白名單或 payload 含 PII 時
    """

    # ── Step 1: 驗證 action_type 合法性 ────────────────────────
    if action_type not in VALID_ACTION_TYPES:
        raise ValueError(
            f"不支援的動作類型：'{action_type}'。"
            f"合法動作為：{', '.join(VALID_ACTION_TYPES)}"
        )

    # ── Step 2: Guardrails PII 防呆驗證 ────────────────────────
    # 確保自動化動作的目標參數中，不包含任何未遮蔽的敏感個資
    is_safe, reason = _validate_payload_no_pii(payload)
    if not is_safe:
        log.warning(f"[ACTION] Guardrails 阻斷 {action_type} 執行 — 原因: {reason}")
        raise ValueError(f"[Guardrails 阻斷] {reason}")

    log.info(f"[ACTION] 開始執行 {action_type} — Payload: {payload}")

    # ── Step 3: 依動作類型分派執行 ──────────────────────────────
    dispatch_map = {
        ACTION_CREATE_CAPA:     _simulate_create_capa,
        ACTION_BLOCK_IP:        _simulate_block_ip,
        ACTION_NOTIFY_SUPPLIER: _simulate_notify_supplier,
    }

    handler = dispatch_map[action_type]
    result  = await handler(payload)

    log.info(f"[ACTION] {action_type} 執行成功 — 結果摘要: {result.get('result', '')[:80]}")
    return result


# ====== 自動生成的測試執行區塊 ======
if __name__ == "__main__":
    st.write("---")
    st.subheader("函數測試區塊")
