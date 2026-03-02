#!/usr/bin/env bash
# POST test data to the running triage API. Start the API first with scripts/run_api.sh
# Optional: BASE_URL=http://localhost:9000 ./scripts/post_triage.sh
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(dirname "$SCRIPT_DIR")"
BASE_URL="${BASE_URL:-http://localhost:8000}"
curl -s -X POST "${BASE_URL}/v1/triage" \
  -H "Content-Type: application/json" \
  -d @"${SCRIPT_DIR}/test_data_input.json"
