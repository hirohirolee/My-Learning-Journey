"""
Probe the actual columns of master_reviews_enriched by inserting a minimal record.
Runs in dry-run mode – prints the schema then exits.
"""
import os
from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

from supabase import create_client

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
TABLE = os.environ.get("SUPABASE_TABLE_NAME", "master_reviews_enriched")

client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Fetch a few rows to see what columns exist
response = client.table(TABLE).select("*").limit(3).execute()
print(f"Table: {TABLE}")
if response.data:
    print(f"Columns detected: {list(response.data[0].keys())}")
    for row in response.data:
        print(row)
else:
    print("Table is empty – cannot auto-detect columns.")
    print("Trying a raw insert with only safe columns to probe...")
    try:
        r = client.table(TABLE).insert({"raw_text": "probe"}).execute()
        print("Insert result:", r.data)
    except Exception as e:
        print("Insert error:", e)
