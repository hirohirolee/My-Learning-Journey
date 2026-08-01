import streamlit as st

import re
from typing import Tuple, Dict

class LLMGuardrail:
    """
    LLM 安全護欄 (LLM Guardrails)
    ──────────────────────────────────────────
    負責過濾惡意提示詞注入攻擊 (Prompt Injection) 與地端/雲端個資隱私防護 (PII Masking)
    """

    # Prompt Injection 關鍵字黑名單
    INJECTION_BLACKLIST = [
        "ignore previous instructions",
        "忽略上述指令",
        "顯示系統提示詞",
        "system prompt",
        "you are now",
        "你現在是",
        "ignore the instructions above",
        "忽略前述指令"
    ]

    @classmethod
    def detect_prompt_injection(cls, prompt: str) -> bool:
        """偵測 Prompt 是否包含黑名單中的注入關鍵字"""
        prompt_lower = prompt.lower()
        for pattern in cls.INJECTION_BLACKLIST:
            if pattern in prompt_lower:
                return True
        return False

    @classmethod
    def mask_prompt(cls, prompt: str) -> Tuple[str, Dict[str, str], bool, str]:
        """
        輸入護欄：遮蔽台灣常見個資，並防範 Prompt Injection
        回傳: (masked_prompt, mask_vault, is_blocked, block_reason)
        """
        # 1. 偵測 Prompt Injection
        if cls.detect_prompt_injection(prompt):
            return prompt, {}, True, "安全防護：偵測到惡意提示詞注入行為 (Prompt Injection)，請求已安全阻斷。"

        mask_vault = {}
        masked_prompt = prompt

        # 2. 定義 PII 敏感個資 Regex 規則
        # 台灣身分證字號 (第一個大寫英文字母, 第二個數字為 1 或 2, 後接 8 位數字)
        id_pattern = r"\b[A-Z][12]\d{8}\b"
        # 電子郵件 (Email)
        email_pattern = r"[\w\.-]+@[\w\.-]+\.\w+"
        # 台灣行動電話 (09開頭十位數字，支持有/無破折號格式 09xx-xxx-xxx 或 09xxxxxxxx)
        phone_pattern = r"\b09\d{2}-\d{3}-\d{3}\b|\b09\d{8}\b"

        patterns = {
            "ID_CARD": id_pattern,
            "EMAIL": email_pattern,
            "PHONE": phone_pattern
        }

        # 3. 逐一進行敏感個資遮蔽 (PII Masking)
        for token_name, pattern in patterns.items():
            matches = list(re.finditer(pattern, masked_prompt))
            counter = 1
            unique_matches = {}
            for match in matches:
                val = match.group()
                if val not in unique_matches:
                    unique_matches[val] = f"[{token_name}_{counter}]"
                    counter += 1
            
            # 使用 Token 遮蔽
            for val, token in unique_matches.items():
                masked_prompt = masked_prompt.replace(val, token)
                mask_vault[token] = val

        return masked_prompt, mask_vault, False, ""

    @classmethod
    def unmask_response(cls, response: str, mask_vault: Dict[str, str]) -> str:
        """
        輸出護欄：將 AI 回覆中出現的去識別化 Token 安全還原成原始個資
        """
        unmasked_response = response
        for token, original_val in mask_vault.items():
            unmasked_response = unmasked_response.replace(token, original_val)
        return unmasked_response
