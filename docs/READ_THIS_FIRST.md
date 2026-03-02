# Read This First (for Cursor Agents)

This repo is a **reference implementation** for building event-driven, multi-agent, stochastic decision systems. Use it as a playbook: break down problems, implement within clear boundaries, add tests and evals, document decisions.

## How This Repo Works

- **Layers (strict order):** Sources → Event Bus → Orchestrator → Policy/FSM → Agent → Tools → TraceStore. Data flows one way; no layer-skipping.
- **Contracts:** Every boundary uses Pydantic v2 models; all have a `schema_version` for evolution.
- **Determinism:** Orchestrator logic is deterministic. Stochastic behavior lives only in the agent runner (or Temporal activities). Policy FSM (Transitions) and allowlists are deterministic.
- **Safety:** Idempotency for side effects, circuit breaker for LLM/external calls, DLQ + replay for failed events. No raw PII in logs.
- **Evaluation:** pytest for unit/integration (offline); promptfoo for prompt/output regression (offline runner). All tests run without network.

## 8-Step Workflow for Any New Problem

Follow these steps **before** writing implementation code. Non-trivial changes require a **Problem Breakdown** in `docs/breakdowns/`.

| Step | What to do |
|------|-------------|
| **1** | **Write the Problem Breakdown** — Use `docs/PROBLEM_BREAKDOWN_TEMPLATE.md`. Create a new file in `docs/breakdowns/` (e.g. `0002-my-feature.md`). Fill: objective, event types, state model, policies, agent responsibilities, tools, failure modes, observability, evaluation plan. |
| **2** | **Define contracts (Pydantic)** — Add or update models in `app/contracts/`. Include `schema_version`. Everything crossing a boundary must be a Pydantic model. |
| **3** | **Update policy/FSM** — In `app/policy/`: add states/transitions or guards in the Transitions FSM; update allowlist in `policy_engine.py` if new tools or actions. |
| **4** | **Update agent prompts + PROMPT_VERSION** — In `app/agents/prompts.py`: bump `PROMPT_VERSION`, add/change prompts. Log version in traces. |
| **5** | **Add/modify tools via ToolRegistry** — Implement in `app/tools/` (e.g. `tool_a.py`). Register in the registry. Tools go through: allowlist → idempotency → circuit breaker → retry → trace → validate. |
| **6** | **Wire orchestration/service layer** — In `app/orchestrator/` and `app/services/case_service.py`: connect new events, state transitions, agent calls, and tool execution. Keep orchestrator deterministic. |
| **7** | **Add pytest + promptfoo cases** — New behavior: add tests in `tests/`. Add or update cases in `eval/promptfoo/cases/` and assertions in `promptfooconfig.yaml`. Run offline only. |
| **8** | **Update docs/decisions.md** — Record tradeoffs, why you chose an approach, and (if prompts changed) prompt version and eval impact. |

## Key Paths

- **Entrypoint:** `app/main.py` (FastAPI); `app/api.py` (routes); `app/services/case_service.py` (glue).
- **Contracts:** `app/contracts/`.
- **Orchestrator:** `app/orchestrator/stub.py` (deterministic; Temporal-ready interface).
- **Agent:** `app/agents/agent.py` (PydanticAI wrapper); `app/agents/offline_model.py` (stub for tests/eval).
- **Tools:** `app/tools/registry.py` + `tool_a.py`, `tool_b.py`, `tool_c.py`.
- **Eval:** `eval/promptfoo/` — `runner.py` (offline), `promptfooconfig.yaml`, `cases/`, `schemas/`.

## Running Locally (No External Services)

```bash
uv sync --all-extras
uv run uvicorn app.main:app --reload
uv run pytest
npx promptfoo eval -c eval/promptfoo/promptfooconfig.yaml   # from repo root; offline
```

## Golden Path Checklist (Example Commit)

- [ ] Problem breakdown in `docs/breakdowns/` created or updated.
- [ ] Contracts (Pydantic) added/updated with `schema_version`.
- [ ] Policy/FSM and allowlist updated if needed.
- [ ] Prompts and `PROMPT_VERSION` updated; `docs/decisions.md` and promptfoo cases updated.
- [ ] Tools registered; orchestration wired.
- [ ] pytest and promptfoo pass offline.
- [ ] No PII in logs; redaction applied where needed.
