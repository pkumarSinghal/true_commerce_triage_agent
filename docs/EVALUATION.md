# Evaluation

All evaluation runs **offline**: no network calls. Use stubs (offline model, in-memory bus/store) so CI and local runs are deterministic and fast.

## Running Tests

```bash
uv sync --all-extras
uv run pytest                    # unit + integration
uv run pytest -v tests/          # verbose
npx promptfoo eval -c eval/promptfoo/promptfooconfig.yaml   # prompt/output regression (from repo root)
```

## How to use promptfoo

- **Command (from repo root):** `npx promptfoo eval -c eval/promptfoo/promptfooconfig.yaml`
- **What it does:** Runs the triage pipeline **offline** via `eval/promptfoo/runner.py` with stub Classification and Remediation LLMs; no network; validates `TriageResponse` schema and assertions (e.g. `results.length`, `schema_version`).
- **Data consistency:** The same request payloads are used for (1) **pytest** (`tests/fixtures.py`: `synthetic_request_dict()`, `synthetic_batch1_dict()`, `synthetic_batch2_dict()`), (2) **live API tests** (`scripts/test_data_input.json`, `scripts/test_data_batch1.json`, `scripts/test_data_batch2.json`), and (3) **promptfoo** (inline vars in `eval/promptfoo/promptfooconfig.yaml` and `eval/promptfoo/cases/synthetic.yaml`). Single source of truth for shape is `tests/fixtures.py`; the script JSON files and promptfoo cases mirror it so that **offline eval and local startup/live testing are comparable**.

## Test data

- **Location:** Test data is defined in `tests/fixtures.py`: `SYNTHETIC_ITEMS` (10 items), `synthetic_request_dict()` (3-item dict for backward-compat TestClient/promptfoo), `synthetic_batch1_dict()` and `synthetic_batch2_dict()` (5 items each) for two-batch live tests and promptfoo.
- **Shapes:** Multiple shapes simulate semi-structured ingest: timeout, 404, rate limit, 500, 401, validation, DB error, network unreachable, minimal, and optional fields (source, timestamp). Batch 1 and batch 2 are used by `scripts/run_api_tests.sh` and can be used in promptfoo cases.
- **Tenant:** `tenant_id` is set to `tenant_001` in the synthetic requests for tenant-aware tests.
- **Usage:** Used by `tests/test_orchestrator.py`, `tests/test_triage_api.py`, by promptfoo cases, and by the test harness (`scripts/run_api_tests.sh` with `test_data_batch1.json` / `test_data_batch2.json`). Orchestrator tests inject `RuleBasedClassifier` and `StubRemediationLLM` (and optionally `StubClassificationLLM` for the fallback path) so no real LLM is called; the Classification LLM and Remediation LLM agent paths are exercised only via stubs in CI/local tests. Real LLM calls occur only when running the API without stub injection (e.g. with live LiteLLM/Ollama).

## pytest vs promptfoo

| | pytest | promptfoo |
|---|--------|-----------|
| **Purpose** | Unit and integration: API, orchestrator, policy, tools, idempotency, DLQ/replay | Prompt and agent-output regression: schema, step count, fallback, policy |
| **Runner** | pytest | promptfoo (invokes `eval/promptfoo/runner.py` with JSON; runner uses offline model) |
| **Location** | `tests/` | `eval/promptfoo/` (config, cases, runner, schemas) |
| **Network** | None | None (runner must use offline model only) |

## Metrics That Matter

- **Fallback rate:** When the agent cannot produce valid output, fallback plan is used. Track via trace `outcome=fallback` or `_fallback` on Plan. Goal: low in production; tests assert fallback is triggered when LLM is “down”.
- **Invalid-output rate:** Agent returns non-Pydantic-valid output. Handled by validation + fallback; trace and logs should record. promptfoo can assert valid schema.
- **Tool error rate:** Tool calls that return `success=False`. Trace and circuit breaker; tests for retry and breaker.
- **Cost proxy (optional):** If you log token or call counts, use for budgeting; not required for MVP.
- **MTTR proxy (optional):** Time to resolve or replay; observability and runbooks.

## promptfoo Config and Cases

- **Config:** `eval/promptfoo/promptfooconfig.yaml` — provider points to the offline runner; prompts can be inline or file-based; assertions: schema, contains-json, step count, fallback, no forbidden tool.
- **Cases:** `eval/promptfoo/cases/*.yaml` — each case has `vars` (input to runner) and optional `assert` overrides.
- **Runner:** `eval/promptfoo/runner.py` — receives context (vars) from promptfoo, runs triage pipeline in offline mode with stub Classification and Remediation LLMs, outputs TriageResponse JSON. No network.
- **Schemas:** `eval/promptfoo/schemas/` — exported JSON schema for TriageResponse for assertions.
- **Test data:** promptfoo cases use the same synthetic payloads as pytest and the live test harness (`tests/fixtures.py`, `scripts/test_data_*.json`); see `eval/promptfoo/cases/synthetic.yaml` and inline tests in `promptfooconfig.yaml`. Keeping these in sync ensures offline eval and local API testing are comparable.
