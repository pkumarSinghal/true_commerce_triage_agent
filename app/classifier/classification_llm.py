"""Classification LLM fallback: LiteLLM for when rule-based classifier returns unhandled."""

from app.contracts.triage import ClassificationResult, NormalizedError
from app.core.circuit_breaker import CircuitBreaker

# Prompt version for observability
CLASSIFICATION_PROMPT_VERSION = "1.0"


def _call_llm(normalized: NormalizedError) -> ClassificationResult:
    """Call LiteLLM to classify. Returns ClassificationResult or raises."""
    try:
        import litellm
    except ImportError:
        raise RuntimeError("litellm not installed") from None

    system = (
        "You are a triage classifier. Output exactly two lines: "
        "line 1 = classification label (one word or snake_case), "
        "line 2 = severity score 0.0 to 1.0 (number only)."
    )
    user = f"Error context (tenant_id={normalized.tenant_id}): {normalized.message}\nPayload: {normalized.raw_payload}"
    response = litellm.completion(
        model="ollama/llama3.2",  # default; override via env LITELLM_MODEL
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        max_tokens=50,
    )
    content = (response.choices[0].message.content or "").strip()
    lines = [line.strip() for line in content.split("\n") if line.strip()]
    classification = lines[0][:100] if lines else "unknown"
    try:
        severity = float(lines[1]) if len(lines) > 1 else 0.5
    except (ValueError, TypeError):
        severity = 0.5
    severity = max(0.0, min(1.0, severity))
    return ClassificationResult(
        classification=classification,
        severity_score=severity,
        handled=True,
        item_index=normalized.item_index,
    )


class ClassificationLLMFallback:
    """Classification via LLM when rule-based returns unhandled. Uses circuit breaker."""

    def __init__(self, circuit_breaker: CircuitBreaker | None = None):
        self.circuit_breaker = circuit_breaker or CircuitBreaker()

    def classify(self, normalized: NormalizedError) -> ClassificationResult:
        """Call LLM to classify. On failure or circuit open, return deterministic fallback."""
        if self.circuit_breaker.is_open():
            return ClassificationResult(
                classification="unknown",
                severity_score=0.5,
                handled=True,
                item_index=normalized.item_index,
            )
        try:
            result = _call_llm(normalized)
            self.circuit_breaker.record_success()
            return result
        except Exception:
            self.circuit_breaker.record_failure()
            return ClassificationResult(
                classification="unknown",
                severity_score=0.5,
                handled=True,
                item_index=normalized.item_index,
            )
