# True Commerce Triage Agent

Intelligent event monitoring and triage for True Commerce (multi-tenant). Accepts a batch of semi-structured error payloads, classifies each (ML/rule-based with LLM fallback), assigns severity, and returns structured remediation suggestions.

## Architecture

- **Orchestrator** consumes the request, propagates `tenant_id`, and runs: **Planner** → **Classifier** (rule-based; Classification LLM when unhandled) → **Remediation LLM** (optional RAG) → **Executor**.
- **Classifier** is an independently scalable component (rule-based or ML); when it returns "unhandled", the orchestrator calls a Classification LLM.
- **Remediation** comes from a separate LLM with optional RAG; tenant-aware.
- See [docs/architecture.md](docs/architecture.md) and [docs/decisions.md](docs/decisions.md) for diagrams, assumptions, and outstanding questions.

## Run locally

```bash
uv sync --all-extras
uv run uvicorn app.main:app --reload
```

- **API:** `POST /v1/triage` with JSON body: `{ "tenant_id": "optional", "items": [ { "message": "error text", "code": 500 }, ... ] }`.
- **Health:** `GET /health`.

## Run with Docker

```bash
docker build -t triage-agent .
docker run -p 8000:8000 triage-agent
```

## Local setup (Llama 3.2)

For step-by-step local setup with Ollama and Llama 3.2 (install, model pull, env, run, verify), see [docs/LOCAL_SETUP.md](docs/LOCAL_SETUP.md).

**Environment (Ollama):** `LITELLM_MODEL` (e.g. `ollama/llama3.2`, default in code); optional `OLLAMA_BASE_URL` if not localhost. Unit tests use mocks; for full integration with Ollama, run the app and send requests to `POST /v1/triage`.

## Tests

```bash
uv run pytest tests/ -v
```

All tests run offline (stub Remediation LLM and rule-based classifier).

## CI/CD

- **GitHub Actions:** [.github/workflows/ci.yml](.github/workflows/ci.yml) runs on push/PR to `main` or `master`: ruff lint and pytest.
- **Strategy:** Lint and test on every PR; optional promptfoo step can be added for prompt regression.

## Docs

- [docs/READ_THIS_FIRST.md](docs/READ_THIS_FIRST.md) — workflow and layering.
- [docs/architecture.md](docs/architecture.md) — layer diagram and triage pipeline.
- [docs/LOCAL_SETUP.md](docs/LOCAL_SETUP.md) — local setup with Llama 3.2 (Ollama).
- [docs/decisions.md](docs/decisions.md) — ADRs, assumptions, outstanding questions (data lake stream; context shape).
- [docs/load_testing.md](docs/load_testing.md) — load-testing plan for triage endpoint.
- [docs/TEST_HARNESS.md](docs/TEST_HARNESS.md) — test harness (start app + run API tests in two batches).
