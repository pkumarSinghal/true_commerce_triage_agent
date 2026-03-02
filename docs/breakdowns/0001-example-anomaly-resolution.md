# 0001 — Example: Anomaly Resolution (MVP)

This breakdown describes the MVP behavior: one demo event type (e.g. AnomalyDetected), case lifecycle, agent plan with at least three steps using tools check_status, notify_user, open_ticket, fallback when LLM is down, and DLQ/replay.

---

## 1. Objective + Success Metrics

- **Objective:** Resolve an anomaly by correlating events to a case, deciding a multi-step plan via an agent, and executing tools (check status, notify user, open ticket) under policy and idempotency.
- **Success metrics:** Ingest returns case_id; trace has agent_decision and tool_result entries; fallback triggers when offline/failure; promptfoo cases pass (schema, ≥3 steps, fallback, policy denied).

---

## 2. Event Types + Schemas

- **Event types:** `AnomalyDetected`, `ErrorBatchReceived` (demo).
- **Schema:** `EventEnvelope(event_id, case_id?, tenant_id?, event: CanonicalEvent(event_type, payload))`. CanonicalEvent payload is a dict.
- **Canonical mapping:** API receives event_type + payload; service builds CanonicalEvent and passes to bus.

---

## 3. State Model (CaseState) and Lifecycle

- **CaseState:** case_id, status (CaseStatus), event_count, last_event_type.
- **CaseStatus:** open → triaging → in_progress → resolved → closed.
- **Lifecycle:** FSM (Transitions) advances on event_count and guards; e.g. open + first event → triaging; triaging → in_progress; in_progress + threshold → resolved.

---

## 4. Deterministic Policies (Guards, Allowlists, Budgets)

- **Guards:** FSM transitions; max events before auto-resolve (loop breaker).
- **Allowlists:** Policy engine allows actions: check_status, notify_user, open_ticket, no_op. Denied actions are not executed.
- **Budgets:** None for MVP.

---

## 5. Agent Responsibilities (What Agent Decides vs Deterministic)

- **Agent decides:** Plan (ordered steps: which tools, reason, idempotency_key per step); summary.
- **Deterministic:** Whether an action is allowed (policy); idempotency (skip if key seen); fallback when LLM down or invalid output; circuit breaker cooldown.

---

## 6. Tools (Inputs/Outputs + Idempotency Keys)

| Tool           | Inputs              | Outputs     | Idempotency key source   |
|----------------|---------------------|------------|---------------------------|
| check_status   | idempotency_key, {} | ToolResult | Plan step idempotency_key |
| notify_user    | idempotency_key, {} | ToolResult | Plan step idempotency_key |
| open_ticket    | idempotency_key, {} | ToolResult | Plan step idempotency_key |

---

## 7. Failure Modes + Fallbacks

- **LLM down or invalid output:** Use deterministic fallback plan (e.g. single check_status step); set `_fallback` on Plan; trace outcome fallback.
- **Tool failure:** Retry (tenacity); after threshold, circuit breaker opens; trace failure.
- **Policy denies:** Trace outcome denied; do not execute tool.
- **Unprocessable event:** Send to DLQ with reason; support replay(case_id).

---

## 8. Observability (Trace Fields, Metrics)

- **Trace fields:** case_id, kind (agent_decision | tool_result | policy_check | fallback), step_id, tool_name, outcome, error_category, payload (summary, step count).
- **OTel:** Span names ingest, orchestrator.handle_event, agent.get_plan, tool.execute; attributes case_id, tenant_id, prompt_version, model_name, tool_name, outcome, error_category.
- **Metrics:** (Optional) fallback rate, tool error rate.

---

## 9. Evaluation Plan (Offline Tests + promptfoo Cases)

- **pytest:** test_api_happy (ingest, trace), test_llm_failure_fallback (fallback plan), test_idempotency (duplicate key), test_policy_denies_tool (denied), test_dlq_replay (dlq + replay).
- **promptfoo:** case_001_basic (plan schema, ≥3 steps), case_002_llm_down (fallback triggered), case_003_policy_denied (forbidden tool not in plan or not executed).
- **Assertions:** Output matches Plan schema; steps length ≥ 3; fallback true when LLM down; policy-denied case has no execution of denied tool.
