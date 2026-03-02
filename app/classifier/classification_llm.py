"""Classification LLM fallback: PydanticAI Classification agent when rule-based classifier returns unhandled."""

from app.contracts.triage import ClassificationResult, NormalizedError
from app.core.circuit_breaker import CircuitBreaker
from app.agents.classification_agent import get_classification_agent

# Prompt version for observability
CLASSIFICATION_PROMPT_VERSION = "1.0"


class ClassificationLLMFallback:
    """Classification via PydanticAI agent when rule-based returns unhandled. Uses circuit breaker."""

    def __init__(self, circuit_breaker: CircuitBreaker | None = None):
        self.circuit_breaker = circuit_breaker or CircuitBreaker()

    def classify(self, normalized: NormalizedError) -> ClassificationResult:
        """Call Classification agent to classify. On failure or circuit open, return deterministic fallback."""
        if self.circuit_breaker.is_open():
            return ClassificationResult(
                classification="unknown",
                severity_score=0.5,
                handled=True,
                item_index=normalized.item_index,
            )
        try:
            agent = get_classification_agent()
            prompt = (
                f"Error context (tenant_id={normalized.tenant_id}): {normalized.message}\n"
                f"Payload: {normalized.raw_payload}"
            )
            result = agent.run_sync(prompt)
            out = result.output
            self.circuit_breaker.record_success()
            return ClassificationResult(
                classification=out.classification[:100],
                severity_score=out.severity_score,
                handled=True,
                item_index=normalized.item_index,
            )
        except Exception:
            self.circuit_breaker.record_failure()
            return ClassificationResult(
                classification="unknown",
                severity_score=0.5,
                handled=True,
                item_index=normalized.item_index,
            )
