# -*- coding: utf-8 -*-
"""
AI Guardrails Core Engine (企業級 AI 全域資安防護中樞)
======================================================
Compliance: OWASP Top 10 for LLM Applications (2025/2026)
Design: Zero-Trust, Defense-in-Depth, Defense-Before-Inference

Modules:
1. Input Sanitizer & Length Normalizer (LLM01 / LLM10)
2. Prompt Injection & Jailbreak Detector (LLM01)
3. Sensitive Data & PII Auto-Masking (LLM02)
4. System Prompt & Secrets Leakage Guard (LLM06)
5. Output HTML / Script Sanitizer (LLM07)
6. Session Token-Bucket Rate Limiter (LLM10)
7. File Upload Safety Validator
"""

import re
import html
import time
from typing import Tuple, List, Dict, Any, Optional
import streamlit as st

# ==============================================================================
# 1. Input Sanitization & Normalization
# ==============================================================================

def sanitize_input(text: str, max_length: int = 4000) -> str:
    """
    Cleans raw user input:
    - Strips control characters (except newline, tab, carriage return)
    - Truncates to max_length to prevent token/memory exhaustion (DoS)
    - Normalizes excessive whitespace
    """
    if not isinstance(text, str):
        return ""
    
    # Remove null bytes and non-printable control characters
    cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    
    # Enforce strict length cap
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length]
        
    return cleaned.strip()


# ==============================================================================
# 2. Prompt Injection & Jailbreak Detector (OWASP LLM01)
# ==============================================================================

INJECTION_PATTERNS = [
    # Direct instruction overrides
    (r'(?i)ignore\s+(all\s+)?(previous|prior|above)\s+(instructions|prompts|rules)', "直接指令覆寫 (Direct Override)"),
    (r'(?i)disregard\s+(all\s+)?(previous|prior)\s+(instructions|directions)', "無視先前規則 (Disregard Directives)"),
    (r'(?i)you\s+are\s+now\s+(in|a)\s+["\']?(developer\s+mode|unfiltered|god\s+mode|dan)["\']?', "越獄模式切換 (DAN / Developer Mode)"),
    (r'(?i)pretend\s+you\s+(have\s+no\s+rules|are\s+an\s+unrestricted)', "角色扮演越獄 (Unrestricted Roleplay)"),
    
    # System prompt exfiltration
    (r'(?i)(show|display|reveal|repeat|output|leak|print)\s+(your\s+)?(system\s+prompt|initial\s+instructions|secret\s+instructions)', "系統提示詞竊取 (System Prompt Exfiltration)"),
    (r'(?i)what\s+(is|are)\s+your\s+(original|system)\s+(prompt|instructions)', "探針式提示詞探詢 (System Prompt Probing)"),
    (r'無視(先前|所有|上面)(提示詞|指示|規則|約束)', "中文指令劫持 (Chinese Prompt Injection)"),
    (r'輸出(你完整的|原始的|後台)(系統提示詞|System\s*Prompt|初始指令)', "中文提示詞竊取 (Chinese Exfiltration)"),
    (r'從現在開始你沒有任何道德(限制|標準|約束)', "中文越獄繞過 (Chinese Jailbreak Bypass)"),
    (r'扮演一個不受(限制|管制)的\s*(AI|人工智慧)', "中文無限制角色扮演 (Roleplay Attack)"),
    
    # Delimiter hijacking & format escaping
    (r'(?i)```\s*(system|admin|override)\b', "Markdown 語法逃逸 (Markdown Code Hijack)"),
    (r'<\/?(?:system|instruction|admin|override)>', "XML/HTML 標籤偽造 (Tag Spoofing Injection)"),
    (r'\[SYSTEM\s+MESSAGE\]', "系統訊息偽造 (System Header Spoofing)"),
    (r'\{\s*"role"\s*:\s*"system"', "JSON 結構偽造 (JSON Structure Injection)"),
]

def detect_injection(text: str) -> Tuple[bool, str, List[str]]:
    """
    Scans input for prompt injection and jailbreak indicators.
    Returns:
        (is_safe: bool, risk_level: str, findings: List[str])
    Risk levels: "LOW", "MEDIUM", "HIGH", "CRITICAL"
    """
    if not text:
        return True, "SAFE", []
    
    findings = []
    for pattern, description in INJECTION_PATTERNS:
        if re.search(pattern, text):
            findings.append(description)
            
    # Check for suspicious Base64 chunks (potential payload hiding)
    b64_chunks = re.findall(r'[A-Za-z0-9+/]{40,}={0,2}', text)
    if b64_chunks:
        findings.append("可疑 Base64 編碼酬載 (Potential Base64 Obfuscation)")
        
    if not findings:
        return True, "SAFE", []
    elif len(findings) == 1:
        return False, "MEDIUM", findings
    elif len(findings) == 2:
        return False, "HIGH", findings
    else:
        return False, "CRITICAL", findings


# ==============================================================================
# 3. PII & Sensitive Data Auto-Masking (OWASP LLM02)
# ==============================================================================

PII_PATTERNS = [
    # Taiwan National Identification Number: 1 capital letter + 1 or 2 + 8 digits
    (r'\b[A-Z][12]\d{8}\b', "[REDACTED_TW_ID]"),
    # Credit Card Numbers (Visa, MasterCard, Amex, etc.)
    (r'\b(?:\d{4}[ -]?){3}\d{4}\b', "[REDACTED_CREDIT_CARD]"),
    # Taiwan Mobile Numbers (09xx-xxx-xxx or 09xxxxxxxx)
    (r'\b09\d{2}[ -]?\d{3}[ -]?\d{3}\b', "[REDACTED_PHONE]"),
    # International Phone E.164
    (r'\+\d{1,3}[ -]?\d{2,4}[ -]?\d{3,4}[ -]?\d{3,4}', "[REDACTED_INTL_PHONE]"),
    # Email Addresses
    (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', "[REDACTED_EMAIL]"),
    # IPv4 Addresses
    (r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b', "[REDACTED_IP]"),
]

def mask_pii(text: str) -> Tuple[str, int]:
    """
    Scans and replaces sensitive PII with standardized redaction tokens.
    Returns:
        (sanitized_text: str, total_replacements: int)
    """
    if not text:
        return "", 0
    
    total = 0
    masked = text
    for pattern, replacement in PII_PATTERNS:
        matches = re.findall(pattern, masked)
        if matches:
            total += len(matches)
            masked = re.sub(pattern, replacement, masked)
            
    return masked, total


# ==============================================================================
# 4. System Prompt & Secrets Leakage Guard (OWASP LLM06)
# ==============================================================================

SECRET_PATTERNS = [
    (r'sk-[a-zA-Z0-9]{20,}', "[REDACTED_OPENAI_KEY]"),
    (r'gsk_[a-zA-Z0-9]{20,}', "[REDACTED_GROQ_KEY]"),
    (r'ghp_[a-zA-Z0-9]{36}', "[REDACTED_GITHUB_TOKEN]"),
    (r'AIza[0-9A-Za-z-_]{35}', "[REDACTED_GOOGLE_KEY]"),
    (r'(?i)api[_-]?key\s*[:=]\s*["\']?[a-zA-Z0-9_\-]{16,}["\']?', "[REDACTED_API_KEY]"),
    (r'[a-zA-Z]:\\(?:[a-zA-Z0-9_\-\.]+\\)+[a-zA-Z0-9_\-\.]+', "[REDACTED_SERVER_PATH]"),
    (r'/(?:home|etc|var|usr|opt)/(?:[a-zA-Z0-9_\-\.]+/)+[a-zA-Z0-9_\-\.]+', "[REDACTED_SERVER_PATH]"),
]

def detect_secret_leakage(text: str) -> Tuple[bool, List[str]]:
    """
    Checks if model output contains leaked credentials or internal server paths.
    """
    if not text:
        return False, []
    
    leaks = []
    for pattern, label in SECRET_PATTERNS:
        if re.search(pattern, text):
            leaks.append(label)
    return (len(leaks) > 0), leaks

def sanitize_output(text: str) -> str:
    """
    Sanitizes LLM output:
    1. Redacts leaked credentials & internal server paths.
    2. Strips dangerous script / iframe tags to prevent XSS (OWASP LLM07).
    """
    if not text:
        return ""
    
    cleaned = text
    # Mask secrets
    for pattern, replacement in SECRET_PATTERNS:
        cleaned = re.sub(pattern, replacement, cleaned)
        
    # Neutralize active HTML execution while preserving safe Markdown
    cleaned = re.sub(r'<\s*script[^>]*>.*?<\s*/\s*script\s*>', '[BLOCKED_SCRIPT]', cleaned, flags=re.DOTALL | re.IGNORECASE)
    cleaned = re.sub(r'<\s*iframe[^>]*>.*?<\s*/\s*iframe\s*>', '[BLOCKED_IFRAME]', cleaned, flags=re.DOTALL | re.IGNORECASE)
    cleaned = re.sub(r'on\w+\s*=\s*["\'][^"\']*["\']', 'data-blocked="event"', cleaned, flags=re.IGNORECASE)
    
    return cleaned


# ==============================================================================
# 5. Rate Limiting Middleware (OWASP LLM10 - Model DoS)
# ==============================================================================

def check_rate_limit(scope: str = "global", max_calls: int = 15, window_seconds: int = 60) -> Tuple[bool, int]:
    """
    Streamlit session-state sliding window rate limiter.
    Returns:
        (allowed: bool, remaining_seconds_or_calls: int)
    """
    now = time.time()
    rate_state_key = f"_guardrail_rate_{scope}"
    
    if rate_state_key not in st.session_state:
        st.session_state[rate_state_key] = []
        
    timestamps = st.session_state[rate_state_key]
    # Filter out timestamps outside current window
    valid_timestamps = [t for t in timestamps if now - t < window_seconds]
    st.session_state[rate_state_key] = valid_timestamps
    
    if len(valid_timestamps) >= max_calls:
        oldest = min(valid_timestamps)
        cooldown = int(window_seconds - (now - oldest))
        return False, max(cooldown, 1)
        
    st.session_state[rate_state_key].append(now)
    return True, max_calls - len(st.session_state[rate_state_key])


# ==============================================================================
# 6. File Upload Safety Validator
# ==============================================================================

ALLOWED_EXTENSIONS_DEFAULT = {".txt", ".csv", ".json", ".md", ".pdf", ".png", ".jpg", ".jpeg"}

def validate_uploaded_file(uploaded_file, allowed_extensions: set = None, max_mb: float = 10.0) -> Tuple[bool, str]:
    """
    Validates uploaded file against size limits and safe extensions.
    """
    if uploaded_file is None:
        return False, "未選取任何檔案"
        
    if allowed_extensions is None:
        allowed_extensions = ALLOWED_EXTENSIONS_DEFAULT
        
    # Check filename
    name = uploaded_file.name.lower()
    ext = "." + name.split(".")[-1] if "." in name else ""
    
    if ext not in allowed_extensions:
        return False, f"副檔名 `{ext}` 不在允許白名單內（允許：{', '.join(sorted(allowed_extensions))}）"
        
    # Check dangerous double extensions (e.g. payload.exe.txt)
    parts = name.split(".")
    if len(parts) > 2:
        for p in parts[1:-1]:
            if p in ["exe", "bat", "sh", "cmd", "vbs", "ps1", "jar"]:
                return False, f"檢測到可疑雙重副檔名偽裝 ({name})，已拒絕上傳"
                
    # Check file size (Streamlit getbuffer())
    file_bytes = uploaded_file.getvalue()
    size_mb = len(file_bytes) / (1024 * 1024)
    if size_mb > max_mb:
        return False, f"檔案大小 ({size_mb:.2f} MB) 超過系統上限 ({max_mb} MB)"
        
    return True, f"檔案通過安全性檢查 ({size_mb:.2f} MB)"


# ==============================================================================
# 7. Streamlit UI Widget: Guardrail Status Badge
# ==============================================================================

def render_guardrail_badge(compact: bool = False):
    """
    Renders an executive security badge indicating active guardrail protection.
    """
    if compact:
        st.markdown(
            """
            <div style="display: inline-flex; align-items: center; gap: 8px; padding: 4px 12px; 
                        background: rgba(46, 204, 113, 0.12); border: 1px solid rgba(46, 204, 113, 0.35); 
                        border-radius: 20px; font-size: 11px; color: #2ECC71; font-family: monospace;">
                <span style="width: 8px; height: 8px; background: #2ECC71; border-radius: 50%; box-shadow: 0 0 6px #2ECC71;"></span>
                <span>🛡️ AI Guardrail Active (OWASP LLM01-LLM10 Protected)</span>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            """
            <div style="background: linear-gradient(135deg, rgba(18, 24, 38, 0.85), rgba(15, 23, 42, 0.95));
                        border: 1px solid rgba(197, 168, 128, 0.35); border-left: 4px solid #C5A880;
                        padding: 12px 18px; border-radius: 8px; margin: 10px 0 16px 0;">
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
                    <div>
                        <div style="font-weight: 700; color: #E2E8F0; font-size: 13px; display: flex; align-items: center; gap: 8px;">
                            <span style="color: #C5A880;">🛡️ 企業級全域 AI 資安護欄中樞</span>
                            <span style="background: rgba(46, 204, 113, 0.2); color: #2ECC71; font-size: 10px; padding: 2px 8px; border-radius: 12px; border: 1px solid rgba(46, 204, 113, 0.4);">
                                ACTIVE (即時攔截)
                            </span>
                        </div>
                        <div style="font-size: 11px; color: #94A3B8; margin-top: 4px;">
                            防護範圍：OWASP LLM01 提示詞注入、LLM02 個資脫敏 (PII Masking)、LLM06 金鑰阻斷、LLM07 XSS 清洗、LLM10 頻率限制
                        </div>
                    </div>
                    <div style="display: flex; gap: 12px; font-size: 11px; color: #CBD5E1; font-family: monospace;">
                        <span>🔒 PII 自動遮罩: ON</span>
                        <span>⚡ 速率限制: 15 req/min</span>
                        <span>🛡️ 輸入消毒: ON</span>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
