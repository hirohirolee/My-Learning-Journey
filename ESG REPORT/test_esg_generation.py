# -*- coding: utf-8 -*-
"""
ESG 永續報告書自動化生成系統 - 單元測試與整合驗證腳本
"""

import os
import sys
from modules.data_processor import ESGDataProcessor
from modules.local_ai_manager import ESGLLMManager
from modules.report_builder import ESGReportBuilder
import config

def run_verification():
    print("====== 🚀 開始進行 ESG 報告生成系統驗證 ======")
    
    # 1. 驗證 Excel 解析 (環境數據)
    print("\n⏳ [步驟 1] 正在測試環境 Excel 解析...")
    env_file_path = "ISO_14064_1_Inventory.xlsx"
    if not os.path.exists(env_file_path):
        print(f"⚠️ 找不到 '{env_file_path}'，跳過此項測試。")
        env_data = None
    else:
        try:
            env_data = ESGDataProcessor.process_environmental_excel(
                env_file_path,
                company_name="星光電子製造廠",
                reporting_year="2025",
                baseline_emissions=3571.5
            )
            print("✅ 環境數據解析成功！輸出 JSON 樣貌如下：")
            print(f"總排放量: {env_data['emissions_data']['total_emissions_tCO2e']} tCO2e, YoY: {env_data['emissions_data']['yoy_change_percentage']}%")
        except Exception as e:
            print(f"❌ 環境數據解析失敗: {e}")
            sys.exit(1)
            
    # 2. 驗證 Excel 解析 (人資數據) - 使用模擬空檔案觸發預設值
    print("\n⏳ [步驟 2] 正在測試人資數據解析與預設回退...")
    try:
        # 使用空位元組傳入，以觸發預設備用數據機制
        soc_data = ESGDataProcessor.process_social_excel(
            b"", 
            company_name="星光電子製造廠",
            reporting_year="2025"
        )
        print("✅ 人資數據解析與備用初始化成功！輸出項目數：")
        print(f"培訓指標數: {len(soc_data['social_data']['training_metrics'])}, 離職指標數: {len(soc_data['social_data']['turnover_metrics'])}")
    except Exception as e:
        print(f"❌ 人資數據解析失敗: {e}")
        sys.exit(1)

    # 3. 測試 Ollama 文本生成
    print("\n⏳ [步驟 3] 正在測試地端 Ollama 子章節文本生成 (若地端未運行將自動觸發高階備用文本)...")
    try:
        ai_manager = ESGLLMManager()
        
        # 測試 GRI 305
        print("📝 生成 GRI 305 子章節文本中...")
        sub_305 = ai_manager.generate_chapter_subsections(env_data, "GRI 305", target_words=250)
        print("✅ GRI 305 子章節生成成功！")
        env_data["sub_chapters"] = sub_305
        env_data["ai_text"] = "\n\n".join(sub_305.values())
        
        # 測試 GRI 404
        print("📝 生成 GRI 404 子章節文本中...")
        sub_404 = ai_manager.generate_chapter_subsections(soc_data, "GRI 404", target_words=250)
        print("✅ GRI 404 子章節生成成功！")
        soc_data["sub_chapters"] = sub_404
        soc_data["ai_text"] = "\n\n".join(sub_404.values())
        
    except Exception as e:
        print(f"❌ 文本生成階段出錯: {e}")
        sys.exit(1)

    # 4. 測試 Word 報表編譯與圖表渲染
    print("\n⏳ [步驟 4] 正在測試圖表渲染與 Word 文件組裝封裝...")
    try:
        builder = ESGReportBuilder()
        chapters_data = {
            "GRI 305": env_data,
            "GRI 404": soc_data
        }
        output_file = builder.build_full_report("星光電子製造廠", "2025", chapters_data)
        print("✅ Word 報告書組裝並存檔成功！")
        print(f"📁 檔案輸出路徑: {os.path.abspath(output_file)}")
        print(f"📏 檔案大小: {os.path.getsize(output_file)} 位元組")
    except Exception as e:
        print(f"❌ Word 報告書組裝失敗: {e}")
        sys.exit(1)

    print("\n🎉 ====== 所有後端模組驗證完畢，功能一切正常！ ======")

if __name__ == "__main__":
    run_verification()
