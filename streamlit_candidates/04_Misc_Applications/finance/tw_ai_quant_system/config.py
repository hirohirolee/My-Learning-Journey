import os
from pathlib import Path
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# 專案根目錄與目錄設定
BASE_DIR = Path(__file__).resolve().parent
LOG_DIR = BASE_DIR / 'logs'
DATA_DIR = BASE_DIR / 'data'
MODEL_DIR = BASE_DIR / 'models'
for d in [LOG_DIR, DATA_DIR, MODEL_DIR]:
    d.mkdir(parents=True, exist_ok=True)
    
LOG_FILE = LOG_DIR / 'ai_quant.log'

# LLM / OpenAI API 設定 (請在環境變數或此處填入您的 API Key)
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', 'your-openai-api-key')
LLM_MODEL = "gpt-4o-mini" # 使用較快且便宜的模型進行大量新聞情緒分析

# Ollama 本機模型設定 (免付費、顧隱私)
USE_OLLAMA = True
OLLAMA_BASE_URL = "http://localhost:11434/v1"
OLLAMA_MODEL = "llama3" # 請確認您本機已 pull 此模型 (例如 llama3, qwen2, mistral)

# 交易成本與滑價設定 (台股真實環境模擬)
COMMISSION_RATE = 0.001425 * 0.6  # 假設券商 6 折手續費
TAX_RATE = 0.003  # 證交稅 0.3% (賣出時收取)
SLIPPAGE = 0.001  # 預設滑價 0.1% (模擬真實成交點位落差)

# 網路請求設定
REQUEST_TIMEOUT = 15
MAX_RETRIES = 3

# Web UI 設定
UI_PAGE_TITLE = "AI 台股量化交易系統"
UI_PAGE_ICON = "📈"
UI_LAYOUT = "wide"
