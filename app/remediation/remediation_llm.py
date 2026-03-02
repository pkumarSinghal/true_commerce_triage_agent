"""Remediation LLM: PydanticAI Remediation agent; optional RAG; circuit breaker; tenant-aware."""

from app.contracts.triage import ClassificationResult, NormalizedError, RemediationResult
from app.core.circuit_breaker import CircuitBreaker
from app.remediation.rag_mock import RAGMock
from app.agents.remediation_agent import get_remediation_agent

REMEDIATION_PROMPT_VERSION = "1.0"

FALLBACK_SUGGESTION = "Manual review required."


class RemediationLLM:
    """Remediation suggestion via PydanticAI Remediation agent. Optional RAG; circuit breaker; deterministic fallback."""

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
        """Produce remediation suggestion via Remediation agent. On failure or circuit open, return deterministic fallback."""
        if self.circuit_breaker.is_open():
            return RemediationResult(
                remediation_suggestion=FALLBACK_SUGGESTION,
                item_index=normalized.item_index,
                used_fallback=True,
            )
        rag_context = self.rag.retrieve_for_context(normalized)
        try:
            agent = get_remediation_agent()
            prompt = (
                f"Classification: {classification_result.classification}, severity: {classification_result.severity_score}. "
                f"Message: {normalized.message}. Tenant: {normalized.tenant_id}."
            )
            if rag_context:
                prompt += f"\nDocs:\n{rag_context}"
            result = agent.run_sync(prompt)
            out = result.output
            self.circuit_breaker.record_success()
            return RemediationResult(
                remediation_suggestion=(out.remediation_suggestion or FALLBACK_SUGGESTION)[:1000],
                item_index=normalized.item_index,
                used_fallback=False,
            )
        except Exception:
            self.circuit_breaker.record_failure()
            return RemediationResult(
                remediation_suggestion=FALLBACK_SUGGESTION,
                item_index=normalized.item_index,
                used_fallback=True,
            )
