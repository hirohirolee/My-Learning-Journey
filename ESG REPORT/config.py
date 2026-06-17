# -*- coding: utf-8 -*-
"""
ESG 永續報告書自動化生成系統 - 全域設定檔
"""

import os

# 地端 Ollama AI 設定
MODEL_NAME = 'llama3'
OLLAMA_HOST = 'http://127.0.0.1:11434'

# 報告書輸出設定
OUTPUT_DIR = 'output'

# 企業識別色彩 (用於 Matplotlib 繪圖與 Word 文件樣式)
COLOR_GRI_GREEN = '#2E7D32'  # GRI 綠
COLOR_TECH_BLUE = '#1565C0'  # 科技藍
COLOR_LIGHT_GRAY = '#F5F5F5' # 淺底灰
COLOR_DARK_TEXT = '#212121'  # 內文深灰

# 確保輸出目錄存在
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)
