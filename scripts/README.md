# Scripts

- **run_api.sh** — Start the triage API: `./scripts/run_api.sh`. Optional: `PORT=9000 ./scripts/run_api.sh`.
- **post_triage.sh** — POST test payload to the running API: start the API first, then `./scripts/post_triage.sh`. Optional: `BASE_URL=http://localhost:9000 ./scripts/post_triage.sh`.
- **test_data_input.json** — JSON body for `POST /v1/triage` (same shape as `tests/fixtures.synthetic_request_dict()`).
