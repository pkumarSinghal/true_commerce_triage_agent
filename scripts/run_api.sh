#!/usr/bin/env bash
# Start the triage API server. From repo root: ./scripts/run_api.sh
# Uses Claude by default; set LITELLM_MODEL to override. Requires ANTHROPIC_API_KEY in env or .env.
# Optional: PORT=9000 ./scripts/run_api.sh
set -e
cd "$(dirname "$0")/.."
# Load .env if present (e.g. ANTHROPIC_API_KEY)
[ -f .env ] && set -a && source .env && set +a
PORT="${PORT:-8000}"
# Default to Claude; override with LITELLM_MODEL=ollama/llama3.2 etc. if needed
export LITELLM_MODEL="${LITELLM_MODEL:-anthropic/claude-3-5-sonnet}"
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port "$PORT"
