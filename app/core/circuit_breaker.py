"""In-memory circuit breaker: after N failures in window, open until cooldown."""

import time
from threading import Lock


class CircuitBreaker:
    """Simple circuit breaker. Thread-safe for concurrent requests."""

    def __init__(
        self,
        failure_threshold: int = 3,
        window_seconds: float = 60.0,
        cooldown_seconds: float = 30.0,
    ):
        self.failure_threshold = failure_threshold
        self.window_seconds = window_seconds
        self.cooldown_seconds = cooldown_seconds
        self._failures: list[float] = []
        self._opened_at: float | None = None
        self._lock = Lock()

    def is_open(self) -> bool:
        """Return True if breaker is open (calls should use fallback)."""
        with self._lock:
            now = time.monotonic()
            if self._opened_at is not None:
                if now - self._opened_at >= self.cooldown_seconds:
                    self._opened_at = None
                    self._failures.clear()
                    return False
                return True
            # Prune old failures
            cutoff = now - self.window_seconds
            self._failures = [t for t in self._failures if t > cutoff]
            if len(self._failures) >= self.failure_threshold:
                self._opened_at = now
                return True
            return False

    def record_success(self) -> None:
        """Record a successful call (optional; can help half-open)."""
        with self._lock:
            self._failures.clear()

    def record_failure(self) -> None:
        """Record a failed call."""
        with self._lock:
            now = time.monotonic()
            self._failures.append(now)
            cutoff = now - self.window_seconds
            self._failures = [t for t in self._failures if t > cutoff]
            if len(self._failures) >= self.failure_threshold and self._opened_at is None:
                self._opened_at = now
