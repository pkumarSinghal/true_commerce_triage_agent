"""Stub classifier for tests: returns fixed or configurable results."""

from app.contracts.triage import ClassificationResult, NormalizedError


class MLStubClassifier:
    """Mock classifier for unit tests. Returns fixed classification or always unhandled."""

    def __init__(
        self,
        classification: str = "stub",
        severity: float = 0.5,
        handled: bool = True,
    ):
        self.classification = classification
        self.severity = severity
        self.handled = handled

    def classify(self, normalized: NormalizedError) -> ClassificationResult:
        return ClassificationResult(
            classification=self.classification,
            severity_score=self.severity,
            handled=self.handled,
            item_index=normalized.item_index,
        )
