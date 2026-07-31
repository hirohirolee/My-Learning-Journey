"""
Quick test: write one dummy record to Supabase master_reviews_enriched
and confirm the row appears.
"""

import os
from dotenv import load_dotenv

# Load .env so SUPABASE_URL / SUPABASE_KEY / SUPABASE_TABLE_NAME are available
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

# Import AFTER loading env so the module picks up the vars
from supabase_db import save_pr_report, fetch_all_reports, SUPABASE_TABLE_NAME

print(f"[Info] Target table: {SUPABASE_TABLE_NAME}")

# --- Write test ---
result = save_pr_report(
    review="This is a TEST review from test_supabase_write.py – please delete me!",
    rating=4,
    sentiment="positive",
    risk_percent=12.5,
    report_content="[TEST] Auto-generated test report.",
    engine="test-script",
    embedding=None
)
print(f"[Write] Result: {result}")

# --- Read back the latest record ---
print("\n[Read] Fetching latest 3 rows from Supabase ...")
rows = fetch_all_reports()
for row in rows[:3]:
    print(row)

print("\nDone. Check the rows above to confirm the test record was written.")
