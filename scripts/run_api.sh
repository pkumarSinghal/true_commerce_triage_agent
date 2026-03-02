#!/usr/bin/env bash
# Start the triage API server. From repo root: ./scripts/run_api.sh
# Optional: PORT=9000 ./scripts/run_api.sh
set -e
cd "$(dirname "$0")/.."
PORT="${PORT:-8000}"
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port "$PORT"
