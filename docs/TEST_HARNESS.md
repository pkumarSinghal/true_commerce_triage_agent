# Test harness

Two scripts: one starts the app, the other runs API smoke tests (no pytest). Use the same payloads for live testing and for promptfoo so behavior is comparable.

## Layout

- **Start the app:** `./scripts/run_api.sh` (from repo root). Optional: `PORT=9000 ./scripts/run_api.sh`.
- **Run API tests:** With the app running, in another terminal: `./scripts/run_api_tests.sh`. Optional: `BASE_URL=http://localhost:9000 ./scripts/run_api_tests.sh`.

## How to run

1. Terminal 1: `./scripts/run_api.sh`
2. Terminal 2: `./scripts/run_api_tests.sh`

The test script calls `GET /health` and then `POST /v1/triage` twice (batch 1 and batch 2). It expects HTTP 200 and, for triage, a `results` array length of 5 for each batch. Exits with code 0 on success, non-zero on failure.

## Test data

- **Source of truth:** [tests/fixtures.py](../tests/fixtures.py) defines 10 synthetic items and two batches: `synthetic_batch1_dict()` (5 items), `synthetic_batch2_dict()` (5 items).
- **Live API payloads:** [scripts/test_data_batch1.json](../scripts/test_data_batch1.json) and [scripts/test_data_batch2.json](../scripts/test_data_batch2.json) mirror those batches. [scripts/test_data_input.json](../scripts/test_data_input.json) is the original 3-item payload used by `post_triage.sh`.
- **promptfoo** uses the same shapes (see [EVALUATION.md](EVALUATION.md)); cases can reference the batch payloads for consistency.

Keeping `test_data_batch1.json` and `test_data_batch2.json` in sync with `tests/fixtures.py` ensures offline eval and local startup tests use the same data.
