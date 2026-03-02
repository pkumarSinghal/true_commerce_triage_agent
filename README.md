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

## Environment (Ollama for full integration)

To use a local LLM for Classification and Remediation (e.g. Ollama):

- `LITELLM_MODEL`: e.g. `ollama/llama3.2` (default in code).
- `OLLAMA_BASE_URL` or LiteLLM env: set if Ollama is not on localhost.

Unit tests use mocks and do not call the network. For full integration tests with Ollama, run the app and send requests to `POST /v1/triage` with real payloads.

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
- [docs/decisions.md](docs/decisions.md) — ADRs, assumptions, outstanding questions (data lake stream; context shape).
- [docs/load_testing.md](docs/load_testing.md) — load-testing plan for triage endpoint.
