"""Circuit breaker: opens after N failures, cooldown then closes."""

from app.core.circuit_breaker import CircuitBreaker


def test_breaker_closed_initially() -> None:
    cb = CircuitBreaker(failure_threshold=2, window_seconds=60, cooldown_seconds=10)
    assert cb.is_open() is False


def test_breaker_opens_after_threshold_failures() -> None:
    cb = CircuitBreaker(failure_threshold=2, window_seconds=60, cooldown_seconds=10)
    cb.record_failure()
    assert cb.is_open() is False
    cb.record_failure()
    assert cb.is_open() is True


def test_breaker_stays_open_during_cooldown() -> None:
    cb = CircuitBreaker(failure_threshold=1, window_seconds=1, cooldown_seconds=1000)
    cb.record_failure()
    assert cb.is_open() is True
