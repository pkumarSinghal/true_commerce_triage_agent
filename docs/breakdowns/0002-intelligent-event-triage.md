# 0002 — Intelligent Event Triage

Batch semi-structured error payloads are ingested, normalized by the Planner, classified by an ML/rule-based Classifier (with Classification LLM fallback when unhandled), remediated by a separate Remediation LLM (optional RAG), and returned as a validated TriageResponse by the Executor. Tenant-aware; downstream MCP/Agentic servers receive tenant context.

---

## 1. Objective + Success Metrics

- **Objective:** Ingest a batch of semi-structured error payloads (inconsistent schemas), normalize via Planner, classify via ML/rule-based component (with LLM fallback when unhandled), produce remediation via a separate LLM (optional RAG), and return a validated structured TriageResponse; handle LLM and classifier failures gracefully; operate tenant-aware.
- **Success metrics:** POST /v1/triage returns 200 with TriageResponse; tenant_id propagated; fallback triggers when classifier unhandled or LLM down; circuit breakers open after threshold; pytest and (optional) Ollama integration test pass.

---

## 2. Event Types + Schemas

- **Request:** `TriageRequest(schema_version, tenant_id?, items: list[TriageRequestItem])`. Items are flexible (raw_payload or optional message, source, timestamp; extra="allow").
- **Response:** `TriageResponse(schema_version, tenant_id?, results: list[TriageResult], used_classification_fallback?, used_remediation_fallback?)`. TriageResult: classification, severity_score, remediation_suggestion, item_id, raw_item_index.
- **Internal:** PlanResult(normalized_items with tenant_id); ClassificationResult(classification, severity_score, handled); RemediationResult(remediation_suggestion).

---

## 3. State Model (CaseState) and Lifecycle

- **Minimal for triage:** No full case FSM; optional correlation_id/batch_id per batch for tracing. Tenant context flows through pipeline.

---

## 4. Deterministic Policies (Guards, Allowlists, Budgets)

- **Guards:** Max batch size (e.g. 20); timeouts on LLM calls.
- **Circuit breakers:** Mandatory for Classification LLM and Remediation LLM; after N failures in window, use fallback until cooldown.
- **Budgets:** None for MVP.

---

## 5. Agent Responsibilities (What Agent Decides vs Deterministic)

- **Classifier (ML/rules):** Returns classification, severity, handled vs unhandled. When unhandled, orchestrator calls Classification LLM.
- **Classification LLM (fallback):** Produces classification + severity when classifier does not handle.
- **Remediation LLM:** Produces remediation_suggestion only; may use RAG (tenant-aware).
- **Deterministic:** Orchestrator flow; when to call LLM fallback; fallback content (e.g. unknown, 0.5, "Manual review required"); circuit breaker state.

---

## 6. Tools (Inputs/Outputs + Idempotency Keys)

| Component        | Inputs                    | Outputs                |
|-----------------|---------------------------|------------------------|
| Planner         | TriageRequest items       | PlanResult             |
| Classifier      | NormalizedError (+ tenant)| ClassificationResult   |
| Remediation LLM | Classification + context  | RemediationResult      |
| Executor        | Classification + Remediation per item | TriageResponse |

No side-effect tools; idempotency N/A for pure triage response.

---

## 7. Failure Modes + Fallbacks

- **Classifier unhandled:** Orchestrator calls Classification LLM fallback; if that fails, use deterministic classification (e.g. "unknown", severity 0.5).
- **Classification LLM down or invalid output:** Deterministic fallback per item; set used_classification_fallback; circuit breaker.
- **Remediation LLM down or invalid output:** Deterministic remediation text ("Manual review required"); set used_remediation_fallback; circuit breaker.
- **Circuit breaker open:** All requests in cooldown get fallback for that component.

---

## 8. Observability (Trace Fields, Metrics)

- **Trace fields:** batch_id/correlation_id, tenant_id, prompt_version, outcome (success | fallback), latency, used_classification_fallback, used_remediation_fallback.
- **OTel:** Span attributes case_id (or batch_id), tenant_id, prompt_version, model_name, tool_name, outcome, error_category. No PII in logs; redaction.

---

## 9. Evaluation Plan (Offline Tests + Ollama Integration)

- **pytest:** Happy path (batch with tenant_id, valid response); classifier unhandled → LLM fallback; remediation LLM failure → fallback; circuit breaker after N failures; request validation 422; tenant_id propagated.
- **Integration (Ollama):** Optional full run with LiteLLM → Ollama for Classification and Remediation LLMs.
- **Assertions:** TriageResponse schema; tenant_id in response; fallback flags when mocks fail or return invalid.
