#!/usr/bin/env bash
# POST test data to the running triage API. Start the API first with scripts/run_api.sh
# Sends scripts/test_data_input.json (multiple items with source/timestamp). Logs request and response.
# Optional: BASE_URL=http://localhost:9000 ./scripts/post_triage.sh
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(dirname "$SCRIPT_DIR")"
BASE_URL="${BASE_URL:-http://localhost:8000}"
INPUT_FILE="${INPUT_FILE:-${SCRIPT_DIR}/test_data_input.json}"
echo "POST ${BASE_URL}/v1/triage (input: ${INPUT_FILE})"
echo "--- request (first 500 chars) ---"
head -c 500 "$INPUT_FILE"
echo ""
RESP_FILE="/tmp/post_triage_response.json"
HTTP_CODE=$(curl -s -o "$RESP_FILE" -w "%{http_code}" -X POST "${BASE_URL}/v1/triage" \
  -H "Content-Type: application/json" \
  -d @"${INPUT_FILE}")
echo "--- response (HTTP $HTTP_CODE) ---"
cat "$RESP_FILE"
echo ""
echo "--- response (pretty) ---"
python3 -m json.tool "$RESP_FILE" 2>/dev/null || cat "$RESP_FILE"
