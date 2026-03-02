# Security and Safety

For the current triage MVP, the policy engine and ToolRegistry are not implemented; this document describes the intended safety model for future extension (e.g. when adding tools or event-bus ingest).

## Policy Allowlists

- **Policy engine** (e.g. `app/policy/policy_engine.py` when introduced) enforces which tools/actions are allowed per case (or tenant). Default: allowlist; unknown actions are denied.
- **Orchestrator** would check policy before every tool execution. If denied, trace outcome `denied` and do not call the tool.

## Least Privilege

- Tools receive only the arguments they need (idempotency_key + validated dict). No raw request or full context unless explicitly designed.
- API and services do not expose internal state beyond what is required for the contract.

## Idempotency

- **Mandatory for side effects** (when tools are used). Every tool execution would be keyed by an idempotency key (e.g. case_id + step index). `IdempotencyStore` records seen keys; duplicate key → skip execution, no duplicate side effect.
- Keys must be deterministic from the plan and case so replay produces the same keys.

## Circuit Breaker

- **Mandatory for LLM path and external-like tools.** After N failures, the circuit opens: force fallback (agent) or skip (tool) for a cooldown. Prevents cascade and allows recovery.
- Orchestrator uses a step-based cooldown (no wall-clock in core logic) so workflow remains deterministic and testable.

## DLQ and Replay

- **Required for unprocessable events.** Events that fail processing (e.g. validation, repeated failure) go to the Dead-Letter Queue. Do not drop silently.
- **Replay:** `EventBus.replay(case_id)` returns all events for that case in order. Used to reprocess after fix or for debugging. Document conventions (e.g. idempotency keys prevent duplicate side effects on replay).
