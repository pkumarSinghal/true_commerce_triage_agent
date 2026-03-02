# CI/CD Strategy

## Current state

The pipeline is defined in [.github/workflows/ci.yml](../.github/workflows/ci.yml). On every push or pull request to `main` or `master`:

1. **Sync:** `uv sync --all-extras` installs dependencies.
2. **Lint:** `uv run ruff check app tests` and `uv run ruff format --check app tests` enforce style and import rules.
3. **Test:** `uv run pytest tests/ -v` runs the test suite.

There is no format-on-write step; CI only checks format. Run `uv run ruff format app tests` locally to fix formatting.

No deploy step runs in this repo. The app is containerized via the root [Dockerfile](../Dockerfile); deployment would be configured in a separate pipeline (e.g. Azure, AWS, or internal CI).

## Stages

- **Lint** → **Unit/integration tests (pytest)** → *(optional)* **promptfoo** for prompt regression.
- Optional promptfoo: add a job that runs `npx promptfoo eval -c eval/promptfoo/promptfooconfig.yaml` when you want prompt regression guarded by CI. Today it is run manually; see [EVALUATION.md](EVALUATION.md).

## Branch policy

- CI runs on every PR and on push to `main`/`master`.
- Block merge when lint or tests fail. No merge on red.

## Secrets

Current jobs do not need secrets; LLM-dependent tests use stubs and run offline. If you add promptfoo or e2e steps that call real APIs, store API keys in GitHub secrets and never log or echo them.

## Future options

- **Coverage:** Add `pytest-cov` reporting and upload to Codecov or similar (e.g. `coverage.xml` + Codecov action).
- **Docker:** Add a job to build the image and optionally push to a registry (e.g. GitHub Container Registry or Azure ACR).
- **Deploy:** Deploy to Azure App Service, AKS, or another target from a separate workflow or release pipeline; keep this repo’s CI focused on lint and test.
