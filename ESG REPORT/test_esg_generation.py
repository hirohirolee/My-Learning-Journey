"""
ESG 永續報告書自動化生成系統 - 全指標 78 頁完全體模擬驗證腳本
"""

import sys
import os

if hasattr(sys.stdout, 'reconfigure'):
    try: sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception: pass

from modules.local_ai_manager import ESGLLMManager
from modules.report_builder import ESGReportBuilder
from gri_config import GRI_CONFIG

def generate_full_31_topics_mock(company_name, year):
    """
    為全套 31 個重大議題動態生成長文本包
    """
    print("🎲 正在動態建立符合 31 大主題之專家級永續數據原料包...")
    mock_data = {}
    
    for key, cfg in GRI_CONFIG.items():
        code = cfg["code"]
        sub_dict = {}
        for sub_key, info in cfg["sub_items"].items():
            # 建立 350 字以上的三段式專家文本原料
            sub_dict[sub_key] = (
                f"【第一階段：管理方針(DMA)與核心框架】依據 GRI {code} 報導準則，本公司已正式將「{info['title']}」列為年度最高等級重大性議題。內部由董事長親自督導企業永續發展小組，並訂定嚴格的內控制度與管考關鍵績效指標(KPI)，常態性收集、清洗非財務數據，藉此健全組織治理韌性與永續應變能力。\n"
                f"【第二階段：年度量化數據與深度解讀】本年度在該揭露項目的運作上皆百分之百完全合規。經跨部門協同查核，相關量化指標皆在控制最優化水平，且全年度無任何違反環境法規、勞資糾紛或社會不合規事件。各營運據點與價值鏈關係之運作深度符合 Few-shot 智慧切片技術之稽核宣告，確保資訊高度透明與透明。\n"
                f"【第三階段：持續改進與長期永續宣告】展望未來，本公司將持續落實綠色數位雙軸轉型戰術，深化數據 pre-warning 前置警示系統之實務應用。我們承諾每年度定期發布合規報告，積極響應全球淨零碳排與社會責任之最高宣告，持續型塑誠信永續的企業核心價值文化。"
            )
        
        mock_data[f"GRI {code}"] = {
            "company_name": company_name,
            "reporting_year": year,
            "sub_chapters": sub_dict
        }
    return mock_data

def run_verification():
    print("====== 🚀 開始編譯 78 頁全模組視覺完全體永續報告書 ======")
    target_company = "星光電子製造廠"
    target_year = "2025"
    
    # 獲取 31 個章節的厚實原料
    full_dataset = generate_full_31_topics_mock(target_company, target_year)
    
    print("\n⏳ [步驟 4] 正在啟動後端排版引擎進行全指標多斷頁組裝...")
    try:
        builder = ESGReportBuilder()
        output_file = builder.build_full_report(target_company, target_year, full_dataset)
        print("\n🎉 ====== 恭喜您！78 頁完全體永續報告書草案組裝完畢！ ======")
        print(f"📁 實體 Word 輸出路徑: {os.path.abspath(output_file)}")
    except Exception as e:
        print(f"❌ 組裝失敗: {e}")

if __name__ == "__main__":
    run_verification()