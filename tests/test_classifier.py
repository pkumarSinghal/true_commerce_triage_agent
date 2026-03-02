"""Classifier: rule-based returns handled/unhandled; LLM fallback; circuit breaker."""

from app.contracts.triage import NormalizedError
from app.classifier.rule_based import RuleBasedClassifier
from app.classifier.ml_stub import MLStubClassifier
from app.classifier.classification_llm import ClassificationLLMFallback
from app.core.circuit_breaker import CircuitBreaker


def test_rule_based_returns_handled_for_known_pattern() -> None:
    clf = RuleBasedClassifier()
    norm = NormalizedError(message="Connection timed out", item_index=0)
    r = clf.classify(norm)
    assert r.handled is True
    assert r.classification == "timeout"
    assert 0 <= r.severity_score <= 1


def test_rule_based_returns_unhandled_for_unknown() -> None:
    clf = RuleBasedClassifier()
    norm = NormalizedError(message="Some obscure error xyz123", item_index=0)
    r = clf.classify(norm)
    assert r.handled is False
    assert r.classification == "unknown"


def test_ml_stub_returns_configured_result() -> None:
    clf = MLStubClassifier(classification="stub", severity=0.3, handled=True)
    norm = NormalizedError(message="any", item_index=1)
    r = clf.classify(norm)
    assert r.classification == "stub"
    assert r.severity_score == 0.3
    assert r.handled is True
    assert r.item_index == 1


def test_classification_llm_fallback_returns_deterministic_when_circuit_open() -> None:
    breaker = CircuitBreaker(failure_threshold=1, window_seconds=10, cooldown_seconds=5)
    breaker.record_failure()
    fallback = ClassificationLLMFallback(circuit_breaker=breaker)
    norm = NormalizedError(message="anything", item_index=0)
    r = fallback.classify(norm)
    assert r.classification == "unknown"
    assert r.severity_score == 0.5
    assert r.handled is True
