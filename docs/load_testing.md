# Load Testing (conceptual plan)

- **Targets:** `POST /v1/cases/ingest` and `POST /v1/cases/{case_id}/event` under sustained load. For **Intelligent Event Triage:** `POST /v1/triage` (batch triage endpoint) and `/health`.
- **Tools:** Locust, k6, or Artillery; run against local or staging.
- **Scenarios:** Ramp-up ingest rate; fixed case_id append_event concurrency; mixed. For triage: ramp batch size and RPS; mixed payload sizes; sustained load to validate circuit breaker and fallback behavior; measure classifier vs LLM fallback ratio.
- **SLOs:** Define p95 latency and error rate; run in CI or nightly. For triage: p95 latency, error rate, fallback rate when LLM stressed or unavailable.
- **Observability:** OTel spans and trace store must not become bottleneck; consider sampling at high load. Include `tenant_id` in span attributes (per project rules); avoid logging full payloads (redaction).

