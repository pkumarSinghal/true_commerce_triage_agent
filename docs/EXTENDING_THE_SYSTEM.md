# Extending the System — Cookbook

Use this cookbook to add features without breaking layers or contracts. Always start with a Problem Breakdown in `docs/breakdowns/`.

## Add a New Event Type

1. **Contracts:** Ensure `CanonicalEvent` supports the new `event_type` (payload is `dict`; add validation in canonicalization if needed). Optionally extend `app/contracts/events.py` with a tagged union or discriminator.
2. **Orchestrator:** In `app/orchestrator/stub.py`, handle the new event type in the workflow (e.g. update state, call agent). No new layer.
3. **API:** Ingest routes already accept generic `event_type`; add a demo payload in `GET /v1/demo` if desired.
4. **Tests:** Add pytest for ingest with new event type and expected trace/state. Add promptfoo case if agent behavior should change.

## Add a New Tool

1. **Contracts:** Add `Action` enum value in `app/contracts/decisions.py`. Ensure `ToolCall`/`ToolResult` stay generic (or extend with optional fields).
2. **Policy:** In `app/policy/policy_engine.py`, add the new action to the allowlist (or make it configurable).
3. **Tool implementation:** Create `app/tools/tool_*.py` with a function `(idempotency_key, arguments) -> ToolResult`. Register in `app/services/case_service.py` (or wherever the registry is built) with `registry.register("action_name", handler)`.
4. **Agent:** Update prompts so the agent can propose the new action; ensure fallback plan can include it if needed.
5. **Tests:** pytest for tool execution and policy deny. promptfoo case for “plan includes new tool” or “policy denies new tool” as needed.

## Add a New Policy Guard

1. **Policy FSM:** In `app/policy/fsm.py`, add states/transitions or conditions (Transitions API). Keep logic deterministic.
2. **Policy engine:** In `app/policy/policy_engine.py`, add allowlist/denylist or OPA-ready adapter logic.
3. **Orchestrator:** Call policy before agent or before each tool; skip or fallback when guard fails.
4. **Tests:** pytest for “guard blocks X”; promptfoo for “policy denies” case if agent could have requested the blocked action.

## Add a New Agent Prompt

1. **Prompts:** In `app/agents/prompts.py`, add or change the prompt text. **Bump `PROMPT_VERSION`.**
2. **decisions.md:** Add an entry: what changed, why, and that promptfoo cases were added/updated.
3. **promptfoo:** Add or update cases in `eval/promptfoo/cases/` and assertions in `promptfooconfig.yaml`. Run `promptfoo eval` offline.
4. **Observability:** Ensure `prompt_version` is on spans and in trace payloads.

## Add a promptfoo Regression Case

1. Add a YAML file under `eval/promptfoo/cases/` (e.g. `case_004_new_behavior.yaml`) with `vars` and optional `assert` overrides.
2. In `eval/promptfoo/promptfooconfig.yaml`, add the case to the test list or use a glob. Add assertions: schema match, step count, fallback flag, forbidden tool not present, etc.
3. Run `promptfoo eval` and commit.

## Add New Trace Fields

1. **Contracts:** In `app/contracts/trace.py`, add optional fields to `TraceEntry` (e.g. `cost_proxy`, `model_name`). Bump `schema_version` if you version the trace schema.
2. **Orchestrator / agent / tools:** Where you create `TraceEntry`, set the new fields.
3. **Observability doc:** Update `docs/OBSERVABILITY.md` with the new fields and when they are set.
