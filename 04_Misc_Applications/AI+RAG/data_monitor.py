import pandas as pd
import json
import os

def monitor_factory_data(csv_path="factory_data.csv", threshold_ratio=1.2):
    """解析廠區數據，篩選出耗電量超過基準值特定比例 (預設1.2倍) 的異常紀錄"""
    print(f"[*] 正在分析營運數據: {csv_path} (設定異常閾值: {threshold_ratio} 倍)")
    
    if not os.path.exists(csv_path):
        print(f"[錯誤] 找不到檔案 {csv_path}，請先執行資料生成腳本。")
        return None
        
    try:
        df = pd.read_csv(csv_path)
        
        # 規則過濾：找出 Power_Usage 大於 Baseline_kWh * threshold_ratio 的資料
        anomalies = df[df["Power_Usage"] > df["Baseline_kWh"] * threshold_ratio].copy()
        
        if anomalies.empty:
            print("[+] 檢測完成：目前廠區數據一切正常，未發現超出閾值之異常。\n")
            return None
            
        print(f"[!] 警告：發現 {len(anomalies)} 筆嚴重偏離基準的異常數據！")
        
        # 將異常數據提取並打包成結構化 JSON 字串，以利 LLM 閱讀
        anomalies_list = anomalies.to_dict(orient="records")
        anomalies_json = json.dumps(anomalies_list, ensure_ascii=False, indent=4)
        
        return anomalies_json
        
    except Exception as e:
        print(f"[錯誤] 解析 CSV 數據過程中發生例外：{e}")
        return None

if __name__ == "__main__":
    result = monitor_factory_data()
    if result:
        print(">>> 輸出的異常 JSON 訊號：")
        print(result)
