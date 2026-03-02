#!/usr/bin/env bash
# Run API smoke tests against a running triage API. Start the API first: ./scripts/run_api.sh
# Usage: BASE_URL=http://localhost:8000 ./scripts/run_api_tests.sh
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BASE_URL="${BASE_URL:-http://localhost:8000}"

run_test() {
  local name="$1"
  local method="$2"
  local path="$3"
  local data_file="$4"
  local expected_count="$5"

  if [ "$method" = "GET" ]; then
    resp=$(curl -s -w "\n%{http_code}" "${BASE_URL}${path}")
  else
    resp=$(curl -s -w "\n%{http_code}" -X POST "${BASE_URL}${path}" -H "Content-Type: application/json" -d @"${data_file}")
  fi
  http_code=$(echo "$resp" | tail -n1)
  body=$(echo "$resp" | sed '$d')

  if [ "$http_code" != "200" ]; then
    echo "FAIL $name: expected 200, got $http_code"
    echo "$body" | head -c 500
    exit 1
  fi

  if [ -n "$expected_count" ]; then
    if command -v jq >/dev/null 2>&1; then
      count=$(echo "$body" | jq -r '.results | length')
      if [ "$count" != "$expected_count" ]; then
        echo "FAIL $name: expected results length $expected_count, got $count"
        exit 1
      fi
    fi
  fi

  if [ "$name" = "GET /health" ]; then
    if command -v jq >/dev/null 2>&1; then
      status=$(echo "$body" | jq -r '.status')
      if [ "$status" != "ok" ]; then
        echo "FAIL $name: expected status ok, got $status"
        exit 1
      fi
    fi
  fi

  echo "OK $name"
}

run_test "GET /health" GET "/health" "" ""
run_test "POST /v1/triage batch1" POST "/v1/triage" "${SCRIPT_DIR}/test_data_batch1.json" "5"
run_test "POST /v1/triage batch2" POST "/v1/triage" "${SCRIPT_DIR}/test_data_batch2.json" "5"
echo "All API tests passed."
