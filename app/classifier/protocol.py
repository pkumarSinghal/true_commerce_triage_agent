"""Protocol for classifier: input NormalizedError, output ClassificationResult."""

from typing import Protocol

from app.contracts.triage import ClassificationResult, NormalizedError


class ClassifierProtocol(Protocol):
    """Classifier interface: independently scalable; returns handled vs unhandled."""

    def classify(self, normalized: NormalizedError) -> ClassificationResult:
        """Classify one normalized error. handled=False means orchestrator should use LLM fallback."""
        ...
