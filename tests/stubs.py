"""Test stubs for Classification and Remediation LLMs; no real LLM calls."""

from app.contracts.triage import ClassificationResult, NormalizedError, RemediationResult
from app.remediation.remediation_llm import RemediationLLM


class StubClassificationLLM:
    """Returns fixed ClassificationResult without calling LiteLLM. Same interface as ClassificationLLMFallback."""

    def classify(self, normalized: NormalizedError) -> ClassificationResult:
        return ClassificationResult(
            classification="unknown",
            severity_score=0.5,
            handled=True,
            item_index=normalized.item_index,
        )


class StubRemediationLLM(RemediationLLM):
    """Returns fixed suggestion without calling real LLM."""

    def suggest(self, normalized, classification_result):
        return RemediationResult(
            remediation_suggestion="Check logs and retry.",
            item_index=normalized.item_index,
            used_fallback=False,
        )
