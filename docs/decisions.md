# Decisions (ADRs / tradeoffs)

- **Prompt changes:** Any change to prompts (e.g. in `app/agents/prompts.py` or classifier/remediation LLM prompts) must bump `PROMPT_VERSION` and be noted here. Add or adjust evaluation fixtures when changing prompts.
- **Why Temporal stub:** Avoid Temporal SDK dependency for MVP; same interfaces so production can swap in Temporal workflow.
- **Why Transitions:** Deterministic FSM for case lifecycle; testable and explicit.
- **Why PydanticAI:** Structured outputs and tool calling with Pydantic validation; agent always returns valid Plan/Decision.
- **Why DSPy hook:** Placeholder for prompt/program optimization and eval integration; no DSPy dependency required to run.
- **Why InMemory bus/store:** No network for tests; swap for Azure Event Hubs, Service Bus, and real TraceStore in production.
- **Safety:** Idempotency keys on tool execution; circuit breaker for LLM; retries via tenacity; DLQ/replay conventions on bus.

---

## Triage pipeline

- **Classification as its own component:** ML- or rule-based classifier is a separate component (interface + rule_based/ml_stub) so it can scale independently; avoids LLM cost for known patterns.
- **Classification fallback:** When ML/rules do not handle a case (handled=False), orchestrator calls Classification LLM so novel errors are still classified.
- **Remediation from a different LLM:** Remediation suggestions come from a dedicated Remediation LLM (not the classifier); allows different model/prompt and optional RAG.
- **RAG for remediation:** Remediation LLM can use RAG (mock in-memory or vector store) so docs/runbooks stay up to date; tenant-aware retrieval.
- **Orchestrator / Planner / Executor split:** Orchestrator consumes messages and delegates; Planner normalizes; Executor produces final response; clear separation of concerns.
- **LiteLLM / Ollama:** LiteLLM used for Classification and Remediation LLMs; configurable for Ollama (local) or cloud; no vendor lock-in.

---

## Assumptions (ADR)

1. **Multi-tenant:** True Commerce handles multiple tenants; the system is designed to be tenant-aware. Request/response and internal context carry `tenant_id` where available.
2. **Context carries tenant information:** Ingest context (API or event bus) is assumed to include or be enriched with tenant identification so the pipeline and downstream MCP/Agentic servers can operate tenant-aware (routing, RAG, isolation). If context does not have tenant info, it must be supplied at ingest or treated as single-tenant/default.
3. **Downstream MCP/Agentic servers:** Classification LLM, Remediation LLM, RAG, and any MCP servers are designed to be tenant-aware when context includes tenant_id (e.g. per-tenant RAG, tenant in OTel spans, no cross-tenant leakage).

---

## Outstanding questions (ADR)

1. **Data stream to cloud data lake:** How and when does triage output (or raw events) stream to the cloud data lake (e.g. Snowflake on Azure)? Ownership, format, latency, and integration pattern are **outstanding**; architecture shows the sink conceptually; implementation is optional until resolved.
2. **What information does the context have?** **Outstanding.** Exact shape of ingest context (fields, source of tenant_id, correlation ids) is not fixed. **Working assumption:** context would have tenant information; therefore the architecture is tenant-aware and MCP/Agentic servers downstream are tenant-aware. Validate with product/sources.

