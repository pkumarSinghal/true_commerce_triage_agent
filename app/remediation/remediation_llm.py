"""Remediation LLM: separate LLM for suggestion; optional RAG; circuit breaker; tenant-aware."""

from app.contracts.triage import ClassificationResult, NormalizedError, RemediationResult
from app.core.circuit_breaker import CircuitBreaker
from app.remediation.rag_mock import RAGMock

REMEDIATION_PROMPT_VERSION = "1.0"

FALLBACK_SUGGESTION = "Manual review required."


def _call_remediation_llm(
    normalized: NormalizedError,
    classification_result: ClassificationResult,
    rag_context: str,
) -> RemediationResult:
    """Call LiteLLM for remediation suggestion."""
    try:
        import litellm
    except ImportError:
        raise RuntimeError("litellm not installed") from None

    system = (
        "You are a remediation advisor. Given an error classification and context, "
        "output a short, actionable remediation suggestion (one or two sentences). "
        "Use the provided documentation context if relevant."
    )
    user = (
        f"Classification: {classification_result.classification}, severity: {classification_result.severity_score}. "
        f"Message: {normalized.message}. "
        f"Tenant: {normalized.tenant_id}. "
    )
    if rag_context:
        user += f"\nDocs:\n{rag_context}"
    response = litellm.completion(
        model="ollama/llama3.2",
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        max_tokens=150,
    )
    content = (response.choices[0].message.content or "").strip() or FALLBACK_SUGGESTION
    return RemediationResult(remediation_suggestion=content[:1000], item_index=normalized.item_index)


class RemediationLLM:
    """Remediation suggestion via LLM. Optional RAG; circuit breaker; deterministic fallback."""

    def __init__(
        self,
        circuit_breaker: CircuitBreaker | None = None,
        rag: RAGMock | None = None,
    ):
        self.circuit_breaker = circuit_breaker or CircuitBreaker()
        self.rag = rag or RAGMock()

    def suggest(
        self,
        normalized: NormalizedError,
        classification_result: ClassificationResult,
    ) -> RemediationResult:
        """Produce remediation suggestion. On failure or circuit open, return deterministic fallback."""
        if self.circuit_breaker.is_open():
            return RemediationResult(
                remediation_suggestion=FALLBACK_SUGGESTION,
                item_index=normalized.item_index,
                used_fallback=True,
            )
        rag_context = self.rag.retrieve_for_context(normalized)
        try:
            result = _call_remediation_llm(normalized, classification_result, rag_context)
            self.circuit_breaker.record_success()
            return result
        except Exception:
            self.circuit_breaker.record_failure()
            return RemediationResult(
                remediation_suggestion=FALLBACK_SUGGESTION,
                item_index=normalized.item_index,
                used_fallback=True,
            )
