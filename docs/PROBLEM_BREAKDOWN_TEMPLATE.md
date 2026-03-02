# Problem Breakdown Template

Use this template for every non-trivial change. Save as `docs/breakdowns/NNNN-short-name.md` (e.g. `0002-add-escalation-tool.md`).

---

## 1. Objective + Success Metrics

- **Objective:** (One sentence.)
- **Success metrics:** (e.g. “Fallback rate < 1%”, “All tool calls traced”, “promptfoo cases pass”.)

---

## 2. Event Types + Schemas

- **New or changed event types:** (e.g. `AnomalyDetected`, `ErrorReported`.)
- **Schema:** (Reference `app/contracts/events.py` or list fields: `event_id`, `case_id`, `event_type`, `payload`.)
- **Canonical mapping:** (How raw payloads become `CanonicalEvent`.)

---

## 3. State Model (CaseState) and Lifecycle

- **CaseState / CaseStatus:** (Current states and transitions.)
- **Lifecycle:** (When does case move open → triaging → in_progress → resolved → closed? Guards?)

---

## 4. Deterministic Policies (Guards, Allowlists, Budgets)

- **Guards:** (What must be true before agent is called? Loop limits? Max steps?)
- **Allowlists:** (Which tools/actions are allowed per case or tenant?)
- **Budgets:** (Rate limits, cost caps, step limits—if any.)

---

## 5. Agent Responsibilities (What Agent Decides vs Deterministic)

- **Agent decides:** (e.g. “Which tools to call and in what order”, “Summary text”.)
- **Deterministic (not agent):** (e.g. “Whether tool X is allowed”, “Idempotency key format”, “When to fallback”.)

---

## 6. Tools (Inputs/Outputs + Idempotency Keys)

| Tool | Inputs | Outputs | Idempotency key source |
|------|--------|---------|-------------------------|
| (name) | (Pydantic or dict) | (ToolResult) | (e.g. case_id + step index) |

---

## 7. Failure Modes + Fallbacks

- **LLM down or invalid output:** (Fallback: deterministic plan? Which steps?)
- **Tool failure:** (Retry? Circuit breaker? DLQ?)
- **Policy denies:** (Trace + skip; no tool run.)
- **Unprocessable event:** (DLQ; replay by case_id.)

---

## 8. Observability (Trace Fields, Metrics)

- **Trace fields:** (What to add to `TraceEntry`: e.g. `tool_name`, `outcome`, `error_category`, `prompt_version`.)
- **OTel span names/attributes:** (Required: case_id, tenant_id, prompt_version, model_name, tool_name, outcome, error_category.)
- **Metrics (if any):** (e.g. fallback rate, tool error rate.)

---

## 9. Evaluation Plan (Offline Tests + promptfoo Cases)

- **pytest:** (Which tests? e.g. happy path, fallback, idempotency, policy deny, DLQ/replay.)
- **promptfoo:** (Which cases? e.g. basic plan ≥3 steps, LLM-down triggers fallback, policy-denied forbids tool.)
- **Assertions:** (Schema match, step count, fallback flag, no forbidden tool.)
