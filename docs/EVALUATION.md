# Evaluation

All evaluation runs **offline**: no network calls. Use stubs (offline model, in-memory bus/store) so CI and local runs are deterministic and fast.

## Running Tests

```bash
uv sync --all-extras
uv run pytest                    # unit + integration
uv run pytest -v tests/          # verbose
npx promptfoo eval -c eval/promptfoo/promptfooconfig.yaml   # prompt/output regression (from repo root)
```

## Test data

- **Location:** Test data is defined in `tests/fixtures.py`: `SYNTHETIC_ITEMS` (list of `TriageRequestItem`), `SYNTHETIC_REQUEST` (full `TriageRequest`), and `synthetic_request_dict()` (JSON-serializable dict for TestClient and promptfoo).
- **Shapes:** Three synthetic shapes simulate semi-structured ingest: (1) message + code (e.g. timeout 504), (2) error_detail + path + stack (e.g. 404), (3) minimal (e.g. rate limit). This covers inconsistent payload schemas from real sources.
- **Tenant:** `tenant_id` is set to `tenant_001` in the synthetic request for tenant-aware tests.
- **Usage:** Used by `tests/test_orchestrator.py`, `tests/test_triage_api.py`, and by promptfoo cases (same payloads for consistency). Orchestrator tests inject `RuleBasedClassifier` and `StubRemediationLLM` (and optionally `StubClassificationLLM` for the fallback path) so no real LLM is called; the Classification LLM and Remediation LLM agent paths are exercised only via stubs in CI/local tests. Real LLM calls occur only when running the API without stub injection (e.g. with live LiteLLM/Ollama).

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
- **Test data:** promptfoo cases use the same synthetic payloads as pytest (`tests/fixtures.py` / `synthetic_request_dict()`); see `eval/promptfoo/cases/synthetic.yaml` and inline tests in `promptfooconfig.yaml`.
