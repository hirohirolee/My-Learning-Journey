import json
import os
from http.server import BaseHTTPRequestHandler
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        payload = {
            "status": "ok",
            "runtime": "vercel-python-serverless",
            "supabase_configured": bool(os.environ.get("SUPABASE_URL") and (os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY"))),
            "table_name": os.environ.get("SUPABASE_TABLE_NAME", "master_reviews_enriched"),
            "classifier_exists": (BASE_DIR / "models" / "classifier.pkl").exists(),
            "vectorizer_exists": (BASE_DIR / "models" / "vectorizer.pkl").exists(),
        }
        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)
