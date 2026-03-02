# Load Testing (conceptual plan)

This document describes load-testing targets, tools, scenarios, and SLOs for the triage API and related components.

## Load testing strategy

### Per-component (isolated) load testing

Benchmark components in isolation to find bottlenecks and set baselines without LLM or network variance.

- **Planner:** Stateless. Benchmark `TriagePlanner.plan(request)` with large `items` (e.g. 100–500) and mixed payloads; measure throughput and p95. No LLM.
- **Classifier (rule-based):** Same idea: high request rate with normalized items; measure throughput. No LLM.
- **Classification agent / Remediation agent (PydanticAI):** Call `classification_agent.run_sync(prompt)` or `remediation_agent.run_sync(prompt)` under load (e.g. Locust or k6); measure latency and token/cost proxy. Optionally inject failures to validate circuit breaker and fallback.
- **Orchestrator (stub path):** `TriageOrchestrator.run_triage_from_plan` with stub LLMs to measure orchestration overhead without LLM latency.
- **Executor:** Pure function; benchmark `TriageExecutor.execute(...)` with large result lists.

### End-to-end load testing

- **Target:** `POST /v1/triage` with realistic batch sizes (e.g. 1–50 items per request), ramped RPS.
- **Metrics:** p95 latency, error rate, fallback rate (from response flags or logs), and optionally token/cost.
- **Scenarios:** Ramp batch size; ramp RPS; sustained load to trigger circuit breaker; mixed payload sizes (small vs large `raw_payload`).
- **Tools:** Locust, k6, or Artillery; run against local or staging. Document how to run one scenario (e.g. in `scripts/` or here) so others can reproduce.

### SLOs and observability

Keep or tighten: p95 latency, error rate, fallback rate. At high load, OTel/sampling and redaction (no PII in logs) remain as in the Observability section below.

---

## Targets

- `POST /v1/cases/ingest` and `POST /v1/cases/{case_id}/event` under sustained load.
- **Intelligent Event Triage:** `POST /v1/triage` (batch triage endpoint) and `GET /health`.

## Tools

Locust, k6, or Artillery; run against local or staging.

## Scenarios

- Ramp-up ingest rate; fixed `case_id` append_event concurrency; mixed.
- For triage: ramp batch size and RPS; mixed payload sizes; sustained load to validate circuit breaker and fallback behavior; measure classifier vs LLM fallback ratio.

## SLOs

Define p95 latency and error rate; run in CI or nightly. For triage: p95 latency, error rate, fallback rate when LLM is stressed or unavailable.

## Observability

OTel spans and trace store must not become the bottleneck; consider sampling at high load. Include `tenant_id` in span attributes (per project rules); avoid logging full payloads (redaction).

## Module scaling and overload prevention

How each part of the system can scale and avoid overloading:

- **API / Ingest:** Stateless; scale horizontally. Use optional rate limiting or a max batch size per request (e.g. `items` length cap) to avoid single-request overload.
- **Orchestrator:** Deterministic; scale with worker/process count. Limit batch size so one batch does not exhaust memory; contract already has `max_length=100` on items.
- **Classifier:** Independently scalable (see architecture); rule-based path is cheap; LLM fallback path is protected by circuit breaker. Scale classifier workers separately from LLM workers.
- **LLM (Classification fallback, Remediation):** Circuit breaker (`app/core/circuit_breaker.py`) prevents cascade; document cooldown and failure threshold. Scale via replicas and a queue; limit concurrency per model to avoid thundering herd.
- **Executor / Tools:** Idempotency and ToolRegistry; scale with orchestrator workers. Tool calls are the boundary to protect (retries, circuit breaker).
- **TraceStore / Observability:** At high load use sampling, async/non-blocking writes, and optional buffering so OTel/spans do not become the bottleneck.
- **General:** Backpressure via DLQ for unprocessable events; tune batch size vs RPS tradeoff. SLOs (p95 latency, error rate) map to these modules; define targets per layer where needed.
