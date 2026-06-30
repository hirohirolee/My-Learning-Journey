import requests
import json
import pprint

def run_api_test():
    url = "http://127.0.0.1:8000/api/analyze"
    
    # 準備一個模擬的測試 payload (啟用 mock_mode=True 免 API 金鑰測試)
    payload = {
        "review": "這家牛肉湯真的太棒了！牛肉入口即化，高湯味道清甜，大推牛肉燥飯！",
        "rating": 5,
        "image_base64": None,
        "tone": "標準",
        "mock_mode": True
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    print("=" * 60)
    print("🚀 正在發送測試請求至 FastAPI 伺服器...")
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload, ensure_ascii=False, indent=2)}")
    print("=" * 60)
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        
        print(f"📢 伺服器回應狀態碼: {response.status_code}")
        
        if response.status_code == 200:
            print("🎉 測試成功！以下為伺服器回傳之 JSON 數據：\n")
            pprint.pprint(response.json())
        else:
            print(f"❌ 測試失敗，伺服器回傳錯誤細節：{response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ 連線失敗！請確保您已執行 `python api_server.py` 啟動了 API 伺服器。")
    print("=" * 60)

if __name__ == "__main__":
    run_api_test()
