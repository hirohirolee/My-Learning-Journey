import os
import sys
import json
import urllib.request
import urllib.error
from pathlib import Path

# 確保控制台輸出編碼支援 UTF-8 (特別是 Windows 環境)，避免 Emoji 導致 UnicodeEncodeError
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


# CWA Dataset Constants
DATASETS = {
    "1": {
        "id": "F-C0032-005",
        "name": "台灣各縣市一週天氣預報 (建議替代)",
        "desc": "包含各縣市未來一週的天氣現象、最高溫度、最低溫度等資訊。"
    },
    "2": {
        "id": "F-D0047-091",
        "name": "全臺灣各鄉鎮市區預報資料（未來一週）",
        "desc": "更細緻的鄉鎮級預報，包含溫度、降雨機率、體感溫度等。"
    },
    "3": {
        "id": "C-A0008-001",
        "name": "農業氣象觀測網旬資料",
        "desc": "氣象署與農業部合作的旬資料（每10天更新一次的觀測數據）。"
    }
}

def get_desktop_path():
    """取得當前使用者的桌面路徑"""
    return Path.home() / "Desktop"

def download_weather_data(api_key, dataset_id):
    """
    下載 CWA 資料集並儲存至桌面
    """
    url = f"https://opendata.cwa.gov.tw/fileapi/v1/opendataapi/{dataset_id}?Authorization={api_key}&format=JSON"
    desktop = get_desktop_path()
    output_filename = f"cwa_{dataset_id}_forecast.json"
    output_path = desktop / output_filename
    
    print(f"\n正在從中央氣象署下載資料 (ID: {dataset_id})...")
    print(f"請求 URL: https://opendata.cwa.gov.tw/fileapi/v1/opendataapi/{dataset_id}?Authorization=***&format=JSON")
    
    # 建立請求，加入 User-Agent 避免部分伺服器阻擋
    req = urllib.request.Request(
        url,
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    )
    
    try:
        import ssl
        # 忽略 SSL 憑證驗證，避免 Windows 環境下 certificate verify failed 的錯誤
        ssl_context = ssl._create_unverified_context()
        
        with urllib.request.urlopen(req, context=ssl_context) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))

                
                # 檢查 API 返回的結果是否為錯誤訊息
                # CWA API 有時在 API Key 錯誤時仍會回傳 200 OK，但內容是 JSON 格式的錯誤訊息
                if isinstance(data, dict) and data.get("success") == "false":
                    message = data.get("message", "未知錯誤")
                    print(f"❌ 下載失敗！中央氣象署 API 回傳錯誤：{message}")
                    return False
                
                # 將 JSON 漂亮地寫入檔案
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
                
                print(f"🎉 下載成功！")
                print(f"檔案已儲存至桌面：[cwa_{dataset_id}_forecast.json]({output_path.as_uri()})")
                return True
            else:
                print(f"❌ 下載失敗，HTTP 狀態碼: {response.status}")
                return False
                
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP 錯誤: {e.code} - {e.reason}")
        if e.code == 401:
            print("請檢查您的 API 授權碼（Authorization Key）是否正確。")
        elif e.code == 404:
            print(f"找不到資料集 {dataset_id}，該資料集可能已被下架或不存在。")
        return False
    except urllib.error.URLError as e:
        print(f"❌ 網路連線錯誤: {e.reason}")
        return False
    except json.JSONDecodeError:
        print("❌ 解析 JSON 失敗，回傳資料格式可能不正確。")
        return False
    except Exception as e:
        print(f"❌ 發生非預期錯誤: {e}")
        return False

def main():
    print("=" * 60)
    print("        中央氣象署 (CWA) 開放資料下載器")
    print("=" * 60)
    print("📢 說明：")
    print("原「一週農業氣象預報 (F-A0010-001)」已於中央氣象署平台下架並停止更新。")
    print("本程式提供其他替代方案供您下載。")
    print("-" * 60)
    
    # 讀取 API Key (優先從環境變數或專案配置讀取，若無則提示輸入)
    api_key = os.environ.get("CWA_API_KEY", "").strip()
    if not api_key:
        print("💡 提示：您需要先至中央氣象署氣象資料開放平臺 (https://opendata.cwa.gov.tw/) 註冊會員並取得「授權碼」。")
        api_key = input("請輸入您的中央氣象署 API 授權碼 (Authorization Key): ").strip()
    
    if not api_key:
        print("❌ 未輸入授權碼，程式結束。")
        sys.exit(1)
        
    print("\n請選擇要下載的資料集：")
    for key, info in DATASETS.items():
        print(f" [{key}] {info['name']} ({info['id']})")
        print(f"     說明: {info['desc']}")
    print(" [4] 自訂資料集 ID")
    
    choice = input("\n請輸入選項 (預設為 1): ").strip()
    if not choice:
        choice = "1"
        
    if choice in DATASETS:
        dataset_id = DATASETS[choice]["id"]
    elif choice == "4":
        dataset_id = input("請輸入自訂的資料集 ID (例如 F-C0032-001): ").strip()
        if not dataset_id:
            print("❌ 未輸入資料集 ID，程式結束。")
            sys.exit(1)
    else:
        print("⚠️ 無效的選項，將使用預設的「台灣各縣市一週天氣預報 (F-C0032-005)」")
        dataset_id = DATASETS["1"]["id"]
        
    download_weather_data(api_key, dataset_id)

if __name__ == "__main__":
    main()
