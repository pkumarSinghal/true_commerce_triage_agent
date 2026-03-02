# Handoff checklist

This table maps the repo to common evaluation criteria so reviewers can verify what was implemented.

| Criterion | Where to look / What we did |
|-----------|-----------------------------|
| **System design** | [docs/architecture.md](architecture.md): layer diagram (Mermaid), triage pipeline (API → Planner → Classifier → Remediation → Executor), optional Snowflake/sinks; scalable/resilient (circuit breaker, fallback, tenant-aware). |
| **AI integration** | PydanticAI agents (Classification, Remediation, optional Orchestrator); structured output; tools; LLM failures handled by circuit breaker and fallback (graceful degradation). |
| **Code quality** | Typing (Pydantic at boundaries), logging (Logfire + std logging), modular layers (service, orchestrator, planner, classifier, remediation, executor); [docs/decisions.md](decisions.md) and [docs/EXTENDING_THE_SYSTEM.md](EXTENDING_THE_SYSTEM.md) for inheritance. |
| **Testing** | [tests/](tests/): API ([test_triage_api.py](../tests/test_triage_api.py)), orchestrator ([test_orchestrator.py](../tests/test_orchestrator.py)), classifier, agents ([test_agents.py](../tests/test_agents.py) with TestModel), circuit breaker; [docs/EVALUATION.md](EVALUATION.md); promptfoo for prompt regression. |
| **Evaluation criteria / prompt versioning** | [docs/decisions.md](decisions.md): prompt versioning and promptfoo; PROMPT_VERSION / CLASSIFICATION_PROMPT_VERSION / REMEDIATION_PROMPT_VERSION in code. |
| **Graceful degradation** | Circuit breaker ([app/core/circuit_breaker.py](../app/core/circuit_breaker.py)); fallback classification/remediation on LLM failure; `used_classification_fallback` / `used_remediation_fallback` in response. |
| **Tradeoffs / ADR** | [docs/decisions.md](decisions.md): assumptions, outstanding questions, ML vs LLM, programmatic hand-off, Temporal stub, safety (idempotency, circuit breaker, DLQ). |
| **Containerization** | [Dockerfile](../Dockerfile) at repo root. |
| **CI/CD** | [.github/workflows/ci.yml](../.github/workflows/ci.yml); strategy in [docs/CI_CD_STRATEGY.md](CI_CD_STRATEGY.md). |
| **Version control** | Public repo; commit history shows incremental, logical commits. |

## Pre-handoff

- Run: `uv run ruff check app tests && uv run pytest tests/ -q`
- Run promptfoo if available: `npx promptfoo eval -c eval/promptfoo/promptfooconfig.yaml`
- Ensure README, [architecture.md](architecture.md), and [decisions.md](decisions.md) are current.
