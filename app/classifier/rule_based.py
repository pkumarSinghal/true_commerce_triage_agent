"""Rule-based classifier: keyword/regex rules; returns unhandled for unknown patterns."""

import re
from app.contracts.triage import ClassificationResult, NormalizedError


# Simple rules: (pattern, classification, severity). Order matters (first match).
DEFAULT_RULES: list[tuple[str, str, float]] = [
    (r"timeout|timed out", "timeout", 0.7),
    (r"connection refused|connection reset", "connectivity", 0.8),
    (r"404|not found", "not_found", 0.5),
    (r"500|internal server error", "server_error", 0.9),
    (r"auth|unauthorized|401|403", "auth", 0.8),
    (r"validation|invalid|422", "validation", 0.6),
    (r"rate limit|429", "rate_limit", 0.6),
]


class RuleBasedClassifier:
    """Keyword/regex classifier. Returns handled=False for unknown so orchestrator can use LLM fallback."""

    def __init__(self, rules: list[tuple[str, str, float]] | None = None):
        self.rules = rules or DEFAULT_RULES
        self._compiled = [(re.compile(p, re.I), c, s) for p, c, s in self.rules]

    def classify(self, normalized: NormalizedError) -> ClassificationResult:
        """Match message (and optionally raw_payload) against rules. Unhandled if no match."""
        text = normalized.message + " " + str(normalized.raw_payload)
        for pattern, classification, severity in self._compiled:
            if pattern.search(text):
                return ClassificationResult(
                    classification=classification,
                    severity_score=severity,
                    handled=True,
                    item_index=normalized.item_index,
                )
        return ClassificationResult(
            classification="unknown",
            severity_score=0.5,
            handled=False,
            item_index=normalized.item_index,
        )
