import json
from supabase_db import fetch_all_reports

print("🔍 正在從 Supabase 讀取歷史分析紀錄...")
reports = fetch_all_reports()

if not reports:
    print("❌ 資料庫中目前沒有資料，或者 Supabase 連線尚未設定完成。")
    print("請確認您的 .env 檔案中是否已填入正確的 SUPABASE_KEY 與 SUPABASE_TABLE_NAME。")
else:
    print(f"✅ 成功讀取到 {len(reports)} 筆紀錄：")
    for idx, report in enumerate(reports, 1):
        print(f"\n--- 紀錄 {idx} ---")
        print(f"時間: {report.get('created_at')}")
        print(f"情緒: {report.get('sentiment')}")
        print(f"評分: {report.get('rating')} 顆星")
        print(f"風險: {report.get('risk_percent')}%")
        print(f"評論: {report.get('review')[:50]}...")
