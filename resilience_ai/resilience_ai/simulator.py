import time
import random
import requests

API_URL = "http://localhost:8000/api/v1/trigger_audit"

# 預定義的三種異常情境數據，完全對齊後端 AuditPayload 欄位
SCENARIOS = {
    1: {
        "carbon_intensity": 1.65,
        "user_id": "EHS_Monitor",
        "event_log": "EHS系統偵測：碳排放強度（1.65 kgCO₂e/unit）超標，觸發 ISO 14064-1 稽核程序。",
        "department": "製造一部",
        "shift": "A班",
        "equipment_id": "BOILER-01",
        "production_yield": 92.5
    },
    2: {
        "carbon_intensity": 0.85,
        "user_id": "生管主管",
        "event_log": "MES系統通報：製程良率大跌至 79.3%，低於標準門檻 85%，觸發 SOP-PROD-001 生產稽核。",
        "department": "品保部",
        "shift": "B班",
        "equipment_id": "SMT-LINE-03",
        "production_yield": 79.3
    },
    3: {
        "carbon_intensity": 0.50,
        "user_id": "unknown.user",
        "event_log": "SIEM資安告警：偵測到深夜異常大量下載機密合規資產（2025-01-15 03:42 midnight high-volume download），來源IP 192.168.1.105，觸發 ISO 27001 A.8.16 審計。",
        "department": "資安部",
        "shift": "C班",
        "equipment_id": "SERVER-SEC-01",
        "production_yield": 99.1
    }
}

def send_payload(payload):
    try:
        print(f"\n[+] 準備發射 Payload: {payload}")
        r = requests.post(API_URL, json=payload, timeout=5)
        if r.status_code in (200, 201, 202):
            print(f"    => 成功！後端回應: {r.status_code} - {r.json()}")
        else:
            print(f"    => 失敗！後端回應: {r.status_code} - {r.text}")
    except Exception as e:
        print(f"    => 連線出錯！無法連線至 {API_URL}。錯誤: {e}")

def main():
    print("==================================================")
    print("🛡️  企業數位韌性系統 - 異常數據模擬發射器")
    print(f"📡 目標 API: {API_URL}")
    print("==================================================")
    
    while True:
        print("\n--- 請選擇模擬模式 ---")
        print("[1] 手動模擬 EHS 異常（碳強度超標）")
        print("[2] 手動模擬 MES 異常（良率低下）")
        print("[3] 手動模擬 SIEM 異常（深夜資安威脅）")
        print("[4] 全自動隨機轟擊（每 3 秒自動隨機生成異常，Ctrl+C 終止）")
        print("[0] 離開")
        
        choice = input("請輸入數字 (0-4): ").strip()
        
        if choice == '0':
            print("離開模擬器。")
            break
        elif choice in ('1', '2', '3'):
            scenario_idx = int(choice)
            send_payload(SCENARIOS[scenario_idx])
        elif choice == '4':
            print("\n[*] 啟動全自動隨機轟擊模式！每 3 秒發射一次，請按 Ctrl+C 終止...")
            try:
                while True:
                    scenario_idx = random.choice([1, 2, 3])
                    payload = SCENARIOS[scenario_idx].copy()
                    # 微調數值以增加隨機多樣性
                    if scenario_idx == 1:
                        payload["carbon_intensity"] = round(random.uniform(1.2, 2.5), 2)
                    elif scenario_idx == 2:
                        payload["production_yield"] = round(random.uniform(65.0, 84.0), 1)
                    
                    send_payload(payload)
                    time.sleep(3)
            except KeyboardInterrupt:
                print("\n[!] 隨機轟擊已手動終止。")
        else:
            print("[x] 無效輸入，請重新選擇。")

if __name__ == "__main__":
    main()
