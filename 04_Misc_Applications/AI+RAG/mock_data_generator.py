import pandas as pd
import random
from datetime import datetime, timedelta
import os

def generate_factory_data(csv_path="factory_data.csv"):
    """自動生成包含正常與異常耗電數據的廠區資料 CSV"""
    print(f"[*] 正在生成廠區測試數據: {csv_path}")
    
    try:
        # 生成過去 10 天的資料
        dates = [datetime.today() - timedelta(days=x) for x in range(10, 0, -1)]
        line_ids = ["Line_A", "Line_B"]
        
        data = []
        for date in dates:
            for line in line_ids:
                baseline = random.randint(300, 500)
                
                # 刻意在特定的日期/產線製造異常數據 (大於基準 25%~50%)
                if date.day % 3 == 0 and line == "Line_A":
                    power_usage = int(baseline * random.uniform(1.25, 1.5))
                else:
                    # 正常波動範圍內 (90% ~ 110%)
                    power_usage = int(baseline * random.uniform(0.9, 1.1))
                    
                data.append({
                    "Date": date.strftime("%Y-%m-%d"),
                    "Line_ID": line,
                    "Power_Usage": power_usage,
                    "Baseline_kWh": baseline
                })
                
        df = pd.DataFrame(data)
        df.to_csv(csv_path, index=False, encoding="utf-8-sig")
        print(f"[+] 廠區數據生成完成！共產生 {len(df)} 筆資料。\n")
    except Exception as e:
        print(f"[錯誤] 生成 CSV 資料時發生錯誤：{e}")

def generate_iso_rules(txt_path="iso_14064_1_rules.txt"):
    """生成 ISO 14064-1 相關測試法規與 SOP 條文"""
    print(f"[*] 正在生成 ISO 法規條文: {txt_path}")
    
    rules = """
ISO 14064-1:2018 組織層級溫室氣體排放與移除量化及報告附引導之規範
第 5.2 節 設施變更導致排放量顯著變動之重新評估：
當組織的營運邊界內發生設施變更、設備異常耗能，或發現重大計算錯誤，導致排放量發生顯著變動（如超出歷史基準線 15% 以上）時，必須立即啟動數據重新評估機制，並於系統中詳細記錄變更原因與處置方式。

第 7.3 節 數據品質管理與持續監控：
組織應建立並維持一套嚴謹的監控程序，確保溫室氣體活動數據（包含外購電力等間接能源）的準確度與可追溯性。若發現廠務監測設備傳回之數據存在異常突增波動，應在 24 小時內通報相關稽核與管理單位。

第 8.1 節 矯正與預防措施 (CAPA)：
針對監控過程中發現的數據異常或不符合事項，組織應執行以下措施：
1. 立即處置：停止可能造成過度排放之異常操作，並切換至備援系統進行設備初步檢修。
2. 根因分析：調閱歷史 SCADA 數據、維修紀錄，查明造成能耗數據偏離的根本原因。
3. 長期預防：修訂相關環境管理 SOP，或導入自動化 AI 預警系統，以防止類似事件再次發生。
    """
    
    try:
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(rules.strip())
        print(f"[+] 法規條文檔案生成完成！\n")
    except Exception as e:
        print(f"[錯誤] 寫入法規條文時發生錯誤：{e}")

if __name__ == "__main__":
    generate_factory_data()
    generate_iso_rules()
