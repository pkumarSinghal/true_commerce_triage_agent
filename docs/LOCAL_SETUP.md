# Local setup (Llama 3.2)

Run the app locally with a real LLM (Llama 3.2 via Ollama) and verify behavior end-to-end.

## Prerequisites

- [Ollama](https://ollama.com) installed.
- Python and [uv](https://docs.astral.sh/uv/).

## Model

Pull the model (exact image name may vary; LiteLLM uses `ollama/llama3.2`):

```bash
ollama pull llama3.2
```

## Environment

- **LITELLM_MODEL:** e.g. `ollama/llama3.2` (this is the default in `app/classifier/classification_llm.py` and `app/remediation/remediation_llm.py`).
- **OLLAMA_BASE_URL:** Set only if Ollama is not on localhost.

## Install and run

```bash
uv sync --all-extras
./scripts/run_api.sh
```

Or:

```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Verify

- Run `./scripts/post_triage.sh` (or send `POST /v1/triage` with `scripts/test_data_input.json`). Expect HTTP 200 and a `TriageResponse` JSON with `results` per item.
- For a fuller smoke test, see [docs/TEST_HARNESS.md](TEST_HARNESS.md): start the app, then run `./scripts/run_api_tests.sh`.

## Offline eval without Llama

For offline prompt regression without starting Ollama, run promptfoo; it uses the same payloads as `scripts/test_data_input.json` and the batch files. See [docs/EVALUATION.md](EVALUATION.md).
