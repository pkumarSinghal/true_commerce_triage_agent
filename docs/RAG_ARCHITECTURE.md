# Project: Production-Grade Public RAG Chatbot

Scalable, observable, secure Retrieval-Augmented Generation (RAG) chatbot for public-facing use.

## Core Principles

1. The LLM is the final transformer, not the system.
2. Retrieval quality > prompt cleverness.
3. All outputs grounded in retrieved sources.
4. Observability, evaluation, and guardrails are first-class.
5. Design for modularity and provider abstraction.

---

## LLM Layer

- Use `litellm` for provider abstraction.
- Support OpenAI and Anthropic; support local (e.g. Ollama).
- Enable streaming responses.
- Track token usage and latency per request.

## Embeddings

- Default: `text-embedding-3-large` (OpenAI) or `bge-large`.
- Embeddings versioned.
- Store embedding metadata (source_id, chunk_id, timestamp).

## Vector Store

- Default: Qdrant or pgvector.
- Metadata filtering.
- Hybrid search (vector + keyword).

## Retrieval Pipeline

User Query → Input Validation → Hybrid Retrieval (top_k=20) → Re-ranking (cross-encoder or LLM rerank) → Context compression → LLM → Citation validation → Structured response.

**Do NOT allow:** User → LLM directly without retrieval.

---

## Orchestration

- Prefer custom orchestration: FastAPI + Pydantic.
- LlamaIndex components allowed selectively (retrievers, rerankers).
- Avoid monolithic frameworks.
- All LLM calls use structured outputs when possible.

---

## Guardrails

**Input:** Detect prompt injection; strip instructions that override system rules; enforce max token limits.

**Output:** Responses must cite sources; not fabricate; return "I don't know" if insufficient context.

**Schema:** Pydantic for retrieved context, LLM structured output, API responses.

---

## Evaluation & Monitoring

- **RAGAS** for RAG evaluation: faithfulness, context precision, context recall, answer relevance, synthetic test data. RAGAS is complementary to DSPy (DSPy = build/optimize programs; RAGAS = standardized RAG metrics and datasets). DeepEval allowed as alternative if needed.
- Langfuse or OpenTelemetry for tracing.
- Log: query, retrieved docs, final answer, latency breakdown, token cost.

---

## Backend

- FastAPI, async endpoints, streaming (SSE).
- Redis caching for frequent queries.
- Structured logging (JSON logs).

---

## Frontend

- Streaming tokens.
- Expandable source citations.
- User feedback (thumbs up/down).
- Session memory (short-term only).

---

## Production

- Dockerized.
- Environment-based config.
- Rate limiting, API key protection, CORS configured.

---

## Non-Negotiables

- No hallucinated citations.
- No hidden system prompt leakage.
- No direct LLM answers without retrieval.
- No silent failures.

---

## Mental Model

Information reliability pipeline, not a chatbot. The LLM is a probabilistic renderer constrained by retrieval quality, guardrails, schema validation, and observability. Correctness first, fluency second.

---

## MCP

Support calling MCP servers from different sources to exchange information. Validate all exchanges with Pydantic.
