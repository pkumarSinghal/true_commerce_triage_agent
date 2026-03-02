# Scripts

- **run_api.sh** — Start the triage API: `./scripts/run_api.sh`. Optional: `PORT=9000 ./scripts/run_api.sh`.
- **run_api_tests.sh** — Run API smoke tests (health + two triage batches). Start the API first, then `./scripts/run_api_tests.sh`. Optional: `BASE_URL=http://localhost:9000 ./scripts/run_api_tests.sh`. See [docs/TEST_HARNESS.md](../docs/TEST_HARNESS.md).
- **post_triage.sh** — POST test payload to the running API: start the API first, then `./scripts/post_triage.sh`. Optional: `BASE_URL=http://localhost:9000 ./scripts/post_triage.sh`.
- **test_data_input.json** — JSON body for `POST /v1/triage` (3-item payload; same shape as `tests/fixtures.synthetic_request_dict()`).
- **test_data_batch1.json**, **test_data_batch2.json** — 5-item batches for `run_api_tests.sh`; mirror `tests/fixtures.synthetic_batch1_dict()` and `synthetic_batch2_dict()`.
