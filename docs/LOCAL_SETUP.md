# Local setup (Llama 3.2 or Claude Sonnet)

Run the app locally with a real LLM (Ollama/Llama or Anthropic Claude) and verify behavior end-to-end.

## Prerequisites

- Python and [uv](https://docs.astral.sh/uv/).
- For Llama: [Ollama](https://ollama.com) installed.
- For Claude: an [Anthropic API key](https://console.anthropic.com/).

---

## Claude Sonnet with .env

To use **Claude** (e.g. Claude 3.5 Sonnet) and let the **orchestrator agent** choose tools (classify / remediate) per item:

1. **Create a `.env` file** in the repo root (or copy from `.env.example`):

   ```bash
   # Claude (Anthropic) – required for anthropic/* models
   ANTHROPIC_API_KEY=your-anthropic-api-key-here

   # Model: Claude 3.5 Sonnet via LiteLLM
   LITELLM_MODEL=anthropic/claude-3-5-sonnet
   ```

2. **Start the API** – `scripts/run_api.sh` sources `.env` and defaults to Claude:

   ```bash
   ./scripts/run_api.sh
   ```

   With `LITELLM_MODEL=anthropic/claude-3-5-sonnet`, the app uses the **orchestrator agent**: the LLM receives the tools `classify` and `remediate` and chooses when to call each. This works reliably with Claude; with Llama the same path can hallucinate tool names, so the default for non-Anthropic models is a programmatic loop (no orchestrator LLM).

3. **Optional:** Force orchestrator agent even with a non-Claude model (e.g. for testing):

   ```bash
   USE_ORCHESTRATOR_AGENT=1 LITELLM_MODEL=ollama/llama3.2 ./scripts/run_api.sh
   ```

4. **Verify:** Run `./scripts/post_triage.sh` and check server logs for `triage runner: orchestrator agent` and tool calls.

---

## Llama 3.2 (Ollama)

### Model

Pull the model (LiteLLM uses `ollama/llama3.2`):

```bash
ollama pull llama3.2
```

### Environment

- **LITELLM_MODEL:** e.g. `ollama/llama3.2`. With Llama, the app uses a **programmatic agents loop** (no orchestrator LLM) to avoid tool-name hallucination.
- **OLLAMA_BASE_URL:** Set only if Ollama is not on localhost.

### Install and run

```bash
uv sync --all-extras
# Llama: set model so run_api.sh uses Ollama (or omit and use script default Claude)
LITELLM_MODEL=ollama/llama3.2 ./scripts/run_api.sh
```

Or:

```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## Logging and debug

- **Server logs:** Request/response are logged at INFO. Triage runner choice (orchestrator agent vs programmatic loop) is logged at INFO.
- **Debug agent calls:** Set `LOG_LEVEL=DEBUG` to see per-item classification and remediation agent calls in server logs.

  ```bash
  LOG_LEVEL=DEBUG ./scripts/run_api.sh
  ```

- **post_triage.sh** prints the request (first 500 chars) and the full response (raw and pretty-printed). Use `INPUT_FILE=scripts/test_data_batch1.json ./scripts/post_triage.sh` to send a different payload.

---

## Verify

- Run `./scripts/post_triage.sh` (or send `POST /v1/triage` with `scripts/test_data_input.json`). Expect HTTP 200 and a `TriageResponse` JSON with `results` per item.
- For a fuller smoke test, see [docs/TEST_HARNESS.md](TEST_HARNESS.md): start the app, then run `./scripts/run_api_tests.sh`.

## Offline eval without LLM

For offline prompt regression without starting Ollama/Claude, run promptfoo; it uses the same payloads as `scripts/test_data_input.json` and the batch files. See [docs/EVALUATION.md](EVALUATION.md).
