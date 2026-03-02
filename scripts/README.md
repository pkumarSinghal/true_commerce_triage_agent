# Scripts

- **run_api.sh** — Start the triage API (defaults to Claude; sources `.env`). `./scripts/run_api.sh`. Optional: `PORT=9000`, `LITELLM_MODEL=ollama/llama3.2`. See [docs/LOCAL_SETUP.md](../docs/LOCAL_SETUP.md) for Claude Sonnet + .env.
- **run_api_tests.sh** — Run API smoke tests (health + two triage batches). Start the API first, then `./scripts/run_api_tests.sh`. Optional: `BASE_URL=http://localhost:9000`.
- **post_triage.sh** — POST test payload to the running API; logs request snippet and response (raw + pretty). Start the API first, then `./scripts/post_triage.sh`. Optional: `BASE_URL=...`, `INPUT_FILE=scripts/test_data_batch1.json`.
- **test_data_input.json** — Default JSON body for `POST /v1/triage` (8 items with source/timestamp; used by post_triage.sh).
- **test_data_batch1.json**, **test_data_batch2.json** — 5-item batches for `run_api_tests.sh`.
