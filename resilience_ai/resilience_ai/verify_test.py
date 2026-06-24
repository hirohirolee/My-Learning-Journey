import os
import sys
import asyncio

# 將當前工作目錄加入 Python 路徑，確保能成功 import backend
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def main():
    print("====== 1. 測試 ChromaDB 相對路徑設定 ======")
    from backend.main import DB_PATH
    print(f"[*] 當前工作目錄 (cwd): {os.getcwd()}")
    print(f"[*] 解析出的資料庫相對路徑 (DB_PATH): {DB_PATH}")
    print(f"[*] 資料庫路徑是否存在: {os.path.exists(DB_PATH)}")
    
    print("\n====== 2. 測試雙推論引擎容錯分流 (Try-Except) ======")
    from backend.main import call_ai_inference
    
    # 提醒用戶檢查 GEMINI_API_KEY
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("[!] 提示: 目前偵測到環境變數中沒有 GEMINI_API_KEY，若本地 Ollama 未啟動，雲端備援將無法執行成功。")
    else:
        print("[*] 偵測到 GEMINI_API_KEY 已設定。")

    test_prompt = "請用一句話測試：系統是否正常運作？"
    print(f"[*] 傳送測試 Prompt: '{test_prompt}'")
    print("[*] 開始執行推論（優先嘗試本地 Ollama 3秒連線，失敗則切換 Gemini）...")
    
    try:
        response = await call_ai_inference(test_prompt)
        print("\n====== 3. 測試結果輸出 ======")
        print(f"[+] AI 回應內容:\n{response}")
    except Exception as e:
        print(f"\n[x] 測試過程中發生未預期錯誤: {e}")

if __name__ == "__main__":
    asyncio.run(main())
