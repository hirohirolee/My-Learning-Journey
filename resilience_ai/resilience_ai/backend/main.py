"""
main.py — 企業數位韌性核心後端 API
功能：接收異常數據 → 去識別化 → RAG 檢索 → 本地 AI 推理 → 生成 CAPA 報告
"""

import os
import re
import uuid
import logging
import asyncio
from datetime import datetime
from typing import Optional

import chromadb
import httpx
import requests
import google.genai
from google import genai
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from chromadb.utils import embedding_functions

# ── 日誌設定 ─────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
log = logging.getLogger(__name__)

# ── 常數與資料庫相對路徑設定 ──────────────────────────────────
# 動態計算相對於當前工作目錄的相對路徑，避免寫死絕對路徑，確保地端與 Streamlit Cloud 均能讀取
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_TARGET_DB_PATH = os.path.join(_CURRENT_DIR, "..", "audit_db")
if not os.path.exists(_TARGET_DB_PATH):
    # 若上一層目錄沒有，嘗試尋找同目錄 (backend) 下的 audit_db
    _TARGET_DB_PATH = os.path.join(_CURRENT_DIR, "audit_db")

# 計算出相對於目前工作目錄的相對路徑，傳遞給 ChromaDB
DB_PATH      = os.path.relpath(_TARGET_DB_PATH, os.getcwd())
COLLECTION   = "compliance_rules"
OLLAMA_URL   = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:14b")
EMBED_MODEL  = "nomic-embed-text"

# ── FastAPI 初始化 ────────────────────────────────────────────
app = FastAPI(
    title="企業數位韌性核心後端",
    description="地端私有化 AI 合規稽核系統 | ISO 14064-1 × ISO 27001 × 生管 SOP",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 全域報告快取（生產環境請改用 Redis 或資料庫） ────────────
report_store: dict[str, dict] = {}


# ╔══════════════════════════════════════════════════════════╗
# ║  資料模型（Pydantic Schemas）                            ║
# ╚══════════════════════════════════════════════════════════╝

class AuditPayload(BaseModel):
    carbon_intensity:   float   = Field(..., ge=0, le=10, description="碳排放強度 kgCO₂e/unit")
    user_id:            str     = Field(..., min_length=1, description="操作人員 ID")
    event_log:          str     = Field(..., description="資安事件日誌原始內容")
    department:         Optional[str] = Field(None, description="部門代碼")
    shift:              Optional[str] = Field(None, description="班別（A/B/C）")
    equipment_id:       Optional[str] = Field(None, description="設備編號")
    production_yield:   Optional[float] = Field(None, ge=0, le=100, description="良率 %")

class AuditStatus(BaseModel):
    task_id:    str
    status:     str
    created_at: str
    report:     Optional[dict] = None


# ╔══════════════════════════════════════════════════════════╗
# ║  核心功能模組                                            ║
# ╚══════════════════════════════════════════════════════════╝

def anonymize(payload: AuditPayload) -> dict:
    """
    資料去識別化（Data Anonymization）
    ─────────────────────────────────
    規則：
    1. 員工 ID → 保留部門前綴 + 隱碼後半
    2. 設備 ID → 保留設備類型 + 序號隱碼
    3. 事件日誌 → 移除 IP 位址、email、身分證字號
    """
    # 1. 員工 ID 匿名化
    uid = payload.user_id
    if len(uid) > 4:
        safe_uid = uid[:2] + "***" + uid[-2:]
    else:
        safe_uid = "ANON_OP"

    # 2. 日誌去識別化：移除 IP、email
    safe_log = payload.event_log
    safe_log = re.sub(r"\b\d{1,3}(\.\d{1,3}){3}\b", "[IP_REMOVED]", safe_log)
    safe_log = re.sub(r"[\w\.-]+@[\w\.-]+\.\w+", "[EMAIL_REMOVED]", safe_log)
    safe_log = re.sub(r"[A-Z]\d{9}", "[ID_REMOVED]", safe_log)

    # 3. 設備 ID 匿名化
    safe_eq = payload.equipment_id
    if safe_eq and len(safe_eq) > 4:
        safe_eq = safe_eq[:3] + "***"

    return {
        "user_id":         safe_uid,
        "event_log":       safe_log,
        "equipment_id":    safe_eq,
        "carbon_intensity": payload.carbon_intensity,
        "department":      payload.department or "UNKNOWN_DEPT",
        "shift":           payload.shift or "UNKNOWN_SHIFT",
        "yield_rate":      payload.production_yield,
    }


def risk_assessment(carbon: float, log_text: str, yield_rate: Optional[float]) -> dict:
    """
    規則式風險評級引擎（Rule-Based Risk Engine）
    在 AI 推理之前先快速評級，確保緊急事件立即觸發
    """
    level   = 1
    reasons = []
    flags   = []

    # 碳排放評估
    if carbon > 2.0:
        level = max(level, 3)
        reasons.append(f"碳排放強度 {carbon:.2f} 嚴重超標（上限 1.0，超標 {carbon-1.0:.2f}）")
        flags.append("CARBON_CRITICAL")
    elif carbon > 1.0:
        level = max(level, 2)
        reasons.append(f"碳排放強度 {carbon:.2f} 超標（上限 1.0）")
        flags.append("CARBON_EXCEED")

    # 資安事件評估
    midnight_keywords = ["midnight", "deep night", "深夜", "23:", "00:", "01:", "02:", "03:", "04:", "05:"]
    download_keywords = ["download", "下載", "export", "匯出"]
    if any(k in log_text.lower() for k in midnight_keywords) and \
       any(k in log_text.lower() for k in download_keywords):
        level = max(level, 3)
        reasons.append("偵測到深夜大量下載行為，符合 ISO 27001 A.8.16 重大資安事件判定條件")
        flags.append("SECURITY_MIDNIGHT_DOWNLOAD")

    # 良率評估
    if yield_rate is not None and yield_rate < 85:
        level = max(level, 2)
        reasons.append(f"生產良率 {yield_rate:.1f}% 低於目標值 85%")
        flags.append("YIELD_BELOW_TARGET")

    level_map = {1: "Level-1 輕微", 2: "Level-2 嚴重", 3: "Level-3 緊急停線"}
    response_time = {1: "4 小時內提交 CAPA", 2: "1 小時內初評 / 24 小時完成根因分析", 3: "立即通報廠長 + 資安稽核"}

    return {
        "risk_level":    level,
        "risk_label":    level_map.get(level, "未知"),
        "flags":         flags,
        "reasons":       reasons,
        "response_time": response_time.get(level, ""),
    }


def retrieve_context(query: str, n_results: int = 5) -> str:
    """
    從 ChromaDB 向量資料庫檢索相關 ISO 條文與 SOP
    """
    try:
        ef = embedding_functions.DefaultEmbeddingFunction()
        client = chromadb.PersistentClient(path=DB_PATH)
        collection = client.get_or_create_collection(
            name=COLLECTION,
            embedding_function=ef
        )
        results = collection.query(query_texts=[query], n_results=n_results)
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]

        context_parts = []
        for doc, meta in zip(docs, metas):
            source = meta.get("source", "unknown")
            context_parts.append(f"【來源：{source}】\n{doc}")

        return "\n\n---\n\n".join(context_parts)

    except Exception as e:
        log.warning(f"⚠️  向量檢索失敗，使用備援知識：{e}")
        return (
            "ISO 14064-1：碳排放強度上限為 1.0 kgCO₂e/unit，超標觸發 CAPA 流程。\n"
            "ISO 27001 A.8.16：深夜異常大量下載視為重大資安事件，須立即隔離帳號。\n"
            "SOP-PROD-001：製程異常 4 小時內提交 CAPA 報告。"
        )


async def call_ai_inference(prompt: str) -> str:
    """
    動態容錯雙推論引擎 (Try-Except 雙軌制)
    優先嘗試調用本地的 Ollama (qwen2.5:14b)，並設定 3 秒的短連線超時 (connect timeout)。
    如果發生連線錯誤或超時，自動無痛切換至雲端備援方案 (google-genai SDK 呼叫 gemini-2.5-flash)。
    """
    try:
        log.info(f"🤖 嘗試呼叫本地 Ollama ({OLLAMA_MODEL})...")
        # 設定 3 秒連線超時，120 秒讀取超時
        timeout_settings = httpx.Timeout(connect=3.0, read=120.0, write=120.0, pool=3.0)
        async with httpx.AsyncClient(timeout=timeout_settings) as client:
            resp = await client.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model":  OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.3, "num_predict": 1500}
                }
            )
            resp.raise_for_status()
            result = resp.json().get("response", "AI 回應解析失敗")
            print("[Mode: Local]")  # 本機成功時輸出 [Mode: Local]
            log.info("🟢 [Mode: Local] 本地 Ollama 推理成功")
            return result
    except (httpx.ConnectError, httpx.ConnectTimeout, httpx.TimeoutException, httpx.RequestError) as e:
        log.warning(f"⚠️ 本地 Ollama 連線失敗或超時 (3秒)：{e}。啟動雲端備援方案...")
        return await call_gemini_fallback(prompt)
    except Exception as e:
        log.warning(f"⚠️ 本地 Ollama 發生未知錯誤：{e}。啟動雲端備援方案...")
        return await call_gemini_fallback(prompt)


async def call_gemini_fallback(prompt: str) -> str:
    """
    雲端備援推論函數：使用 2026 最新官方 google-genai SDK 調用 gemini-2.5-flash
    """
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("環境變數 GEMINI_API_KEY 未設定，無法使用雲端備援模型")

        log.info("☁️ 呼叫雲端備援模型 gemini-2.5-flash...")
        # 初始化 2026 最新官方 google-genai SDK
        client = genai.Client(api_key=api_key)
        
        # 使用 aio 進行非同步呼叫，避免阻塞
        response = await client.aio.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        print("[Mode: Cloud]")  # 切換雲端成功時輸出 [Mode: Cloud]
        log.info("🟢 [Mode: Cloud] 雲端 Gemini 2.5 Flash 推理成功")
        return response.text
    except Exception as e:
        log.error(f"❌ 雲端備援推理失敗：{e}")
        return f"[AI 暫時離線] 錯誤訊息：地端與雲端模型皆無法使用。最後錯誤：{str(e)}"


async def run_audit(task_id: str, payload: AuditPayload):
    """
    完整稽核流程（非同步背景執行）
    步驟：去識別化 → 風險評級 → RAG 檢索 → AI 推理 → 報告存儲
    """
    log.info(f"🔍 [{task_id}] 稽核任務啟動")
    report_store[task_id]["status"] = "processing"

    try:
        # Step 1: 去識別化
        safe_data = anonymize(payload)
        log.info(f"🔒 [{task_id}] 去識別化完成")

        # Step 2: 風險評級
        risk = risk_assessment(
            payload.carbon_intensity,
            payload.event_log,
            payload.production_yield
        )
        log.info(f"⚠️  [{task_id}] 風險評級：{risk['risk_label']}")

        # Step 3: RAG 向量檢索
        query = (
            f"碳排放 {payload.carbon_intensity} 超標 "
            f"資安事件 {payload.event_log[:50]} "
            f"CAPA 矯正預防措施"
        )
        context = retrieve_context(query)
        log.info(f"📚 [{task_id}] 向量檢索完成，上下文長度：{len(context)} 字元")

        # Step 4: 組裝 Prompt
        prompt = f"""
你是一位同時具備 ISO 14064-1 碳管理、ISO 27001 資訊安全與製造業生產管制專長的企業合規顧問。
請根據以下資訊，產出一份**繁體中文**的標準 CAPA 矯正預防報告。

## 企業合規知識庫（ISO 條文與 SOP 摘要）
{context}

## 當前異常事件資料（已去識別化）
- 操作人員：{safe_data['user_id']}（{safe_data['department']}，{safe_data['shift']}班）
- 碳排放強度：{safe_data['carbon_intensity']:.2f} kgCO₂e/unit
- 設備編號：{safe_data.get('equipment_id', 'N/A')}
- 良率：{safe_data.get('yield_rate', 'N/A')}%
- 資安日誌：{safe_data['event_log']}

## 風險評級結果
- 等級：{risk['risk_label']}
- 判定原因：{'; '.join(risk['reasons'])}
- 要求回應時限：{risk['response_time']}

## 請輸出以下結構的 CAPA 報告（每項須具體、可執行）

### 1. 事件摘要
（簡述事件發生背景，使用 5W1H 格式）

### 2. 直接原因分析
（導致本次異常的直接觸發因素）

### 3. 根本原因分析（5-Why）
（至少進行 3 層 Why 追問）

### 4. 矯正措施（Corrective Action）
| 項次 | 措施內容 | 負責人層級 | 完成時限 |
|------|----------|------------|----------|
（列出 3-5 項具體可執行的矯正行動）

### 5. 預防措施（Preventive Action）
（列出 2-3 項防止復發的系統性改善方案）

### 6. 效果驗證指標
（說明如何量化驗證改善成效）

### 7. 引用法規條文
（明確引用相關 ISO 條文與 SOP 章節）
"""

        # Step 5: AI 推理
        log.info(f"🤖 [{task_id}] 啟動 AI 雙引擎推理...")
        ai_response = await call_ai_inference(prompt)

        # Step 6: 儲存報告
        report_store[task_id].update({
            "status":        "completed",
            "completed_at":  datetime.now().isoformat(),
            "anonymized_data": safe_data,
            "risk_assessment": risk,
            "ai_capa_report":  ai_response,
            "context_used":    context[:500] + "..."
        })
        log.info(f"✅ [{task_id}] 稽核完成，CAPA 報告已生成")

    except Exception as e:
        log.error(f"❌ [{task_id}] 稽核任務失敗：{e}")
        report_store[task_id].update({
            "status": "failed",
            "error":  str(e)
        })


# ╔══════════════════════════════════════════════════════════╗
# ║  API 路由                                                ║
# ╚══════════════════════════════════════════════════════════╝

@app.get("/", tags=["健康檢查"])
async def root():
    return {
        "system":  "企業數位韌性 AI 稽核系統",
        "version": "2.0.0",
        "status":  "online",
        "model":   OLLAMA_MODEL,
        "time":    datetime.now().isoformat()
    }


@app.get("/health", tags=["健康檢查"])
async def health():
    """檢查各子系統狀態"""
    checks = {}

    # 檢查 Ollama
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"{OLLAMA_URL}/api/tags")
            checks["ollama"] = "online" if r.status_code == 200 else "degraded"
    except Exception:
        checks["ollama"] = "offline"

    # 檢查 ChromaDB
    try:
        client = chromadb.PersistentClient(path=DB_PATH)
        cols = client.list_collections()
        checks["chromadb"] = f"online ({len(cols)} collections)"
    except Exception:
        checks["chromadb"] = "offline"

    checks["api"]         = "online"
    checks["active_tasks"] = len([v for v in report_store.values() if v.get("status") == "processing"])

    return checks


@app.post("/api/v1/trigger_audit", tags=["稽核觸發"])
async def trigger_audit(payload: AuditPayload, background_tasks: BackgroundTasks):
    """
    接收異常數據，非同步觸發 AI 稽核流程
    （適用於 Power BI Webhook 或自動化排程呼叫）
    """
    task_id = str(uuid.uuid4())[:8]
    report_store[task_id] = {
        "task_id":    task_id,
        "status":     "queued",
        "created_at": datetime.now().isoformat(),
        "input": {
            "carbon_intensity": payload.carbon_intensity,
            "department":       payload.department,
            "shift":            payload.shift,
        }
    }

    background_tasks.add_task(run_audit, task_id, payload)

    log.info(f"📥 新稽核任務已接收：{task_id}")
    return {
        "status":    "accepted",
        "task_id":   task_id,
        "message":   "稽核任務已非同步觸發，請使用 task_id 查詢結果",
        "query_url": f"/api/v1/report/{task_id}"
    }


@app.get("/api/v1/report/{task_id}", tags=["報告查詢"])
async def get_report(task_id: str):
    """查詢指定任務的稽核報告"""
    if task_id not in report_store:
        raise HTTPException(status_code=404, detail=f"任務 {task_id} 不存在")
    return report_store[task_id]


@app.get("/api/v1/reports", tags=["報告查詢"])
async def list_reports():
    """列出所有稽核任務摘要"""
    return [
        {
            "task_id":    tid,
            "status":     data.get("status"),
            "created_at": data.get("created_at"),
            "risk_level": data.get("risk_assessment", {}).get("risk_label", "待評估")
        }
        for tid, data in sorted(
            report_store.items(),
            key=lambda x: x[1].get("created_at", ""),
            reverse=True
        )
    ]


@app.post("/api/v1/quick_risk", tags=["快速評估"])
async def quick_risk(payload: AuditPayload):
    """
    快速風險評估（同步回應，不啟動 AI 推理）
    適用於即時告警場景
    """
    risk = risk_assessment(
        payload.carbon_intensity,
        payload.event_log,
        payload.production_yield
    )
    return {
        "risk":    risk,
        "suggest": "建議立即觸發 /api/v1/trigger_audit 進行完整 AI 稽核" if risk["risk_level"] >= 2 else "持續監控中"
    }
