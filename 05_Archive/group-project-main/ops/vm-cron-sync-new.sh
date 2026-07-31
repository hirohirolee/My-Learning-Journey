#!/usr/bin/env bash
set -euo pipefail

APP_URL="${APP_URL:-http://127.0.0.1:8080}"
SYNC_URL="${APP_URL%/}/api/ml-dashboard/sync?dry_run=false&force=false"

curl -fsS -X POST "${SYNC_URL}"
printf "\n"
