# Observability

## OpenTelemetry — Required Span Names and Attributes

Create spans for:

- **ingest** — API ingest request (case_id, tenant_id, outcome).
- **orchestrator.handle_event** — One span per event handled (case_id, tenant_id, prompt_version, outcome).
- **agent.get_plan** — Agent invocation (case_id, prompt_version, model_name if any, outcome: attempt | fallback).
- **tool.execute** — Each tool call (case_id, tool_name, outcome, error_category if failed).
- **dlq** — When an event is sent to DLQ (case_id, reason).
- **replay** — When replay(case_id) is invoked (case_id, event_count).

**Required attributes (when available):** `case_id`, `tenant_id`, `prompt_version`, `model_name`, `tool_name`, `outcome`, `error_category`. Do not put PII in attributes.

## Logging — Redaction Rules

- **No raw PII in logs.** Use structured logging (key=value or JSON).
- **Redact:** Personal data, tokens, full message bodies. Log redacted snippets or hashes only.
- **Safe to log:** case_id, event_id, tenant_id (opaque), prompt_version, tool_name, outcome, error codes, trace IDs.
- **Implementation:** Use `app/services/redaction.py` (or equivalent) for any user/content before logging. Observability layer must call redaction before writing to log streams.
