import os
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
import mock_data_generator
import data_monitor
import compliance_agent

def main():
    print("==================================================")
    print("🚀 啟動【廠區數據解析與 ISO 合規 RAG AI 代理系統】")
    print("==================================================")
    
    # 提示使用者確保 Ollama 已經在背景運行
    print("[提示] 本系統目前設定使用本地端免費模型 (Ollama)。")
    print("       請確保您的電腦已安裝 Ollama，並且有下載對應模型 (例如執行過 ollama run llama3)。\n")

    # [階段 1]：準備測試環境與資料庫
    mock_data_generator.generate_factory_data()
    mock_data_generator.generate_iso_rules()
    
    # [階段 2]：執行數據監控引擎
    # 將容忍閾值設為 1.2 倍 (超出標準 20% 即視為異常)
    anomalies_json = data_monitor.monitor_factory_data(threshold_ratio=1.2)
    
    if not anomalies_json:
        print("系統結束：無異常數據需要處理。")
        return
        
    # [階段 3]：啟動 RAG 與 AI 顧問產生預警報告
    # 建立向量資料庫與索引
    vectorstore = compliance_agent.setup_rag_system()
    
    if vectorstore:
        # 將異常 JSON 送入 Agent，檢索法規並生成報告
        report = compliance_agent.generate_compliance_report(anomalies_json, vectorstore)
        
        if report:
            print("==================================================")
            print("⬇️ 【高階企業內控 AI 顧問】自動產生之合規與預警報表 ⬇️")
            print("==================================================")
            print(report)
            print("==================================================")

if __name__ == "__main__":
    main()
