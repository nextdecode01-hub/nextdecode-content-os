from __future__ import annotations

import functools
import logging
import random
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreaker:
    failure_threshold: int = 3
    cooldown_seconds: float = 60.0
    half_open_max_calls: int = 1
    state: CircuitState = field(default=CircuitState.CLOSED)
    failure_count: int = 0
    last_failure_time: Optional[float] = None
    half_open_calls: int = 0

    def record_success(self):
        self.failure_count = 0
        self.state = CircuitState.CLOSED
        self.half_open_calls = 0

    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.monotonic()
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
            self.half_open_calls = 0
            logger.warning("Circuit breaker opened after failure during half-open test")
        elif self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.warning("Circuit breaker OPEN after %d consecutive failures", self.failure_count)

    def can_attempt(self):
        now = time.monotonic()
        if self.state == CircuitState.CLOSED:
            return True
        if self.state == CircuitState.OPEN:
            if self.last_failure_time and (now - self.last_failure_time >= self.cooldown_seconds):
                self.state = CircuitState.HALF_OPEN
                self.half_open_calls = 0
                logger.info("Circuit breaker HALF-OPEN: testing recovery")
                return True
            return False
        return self.half_open_calls < self.half_open_max_calls

    def increment_half_open(self):
        self.half_open_calls += 1


class ProviderChain:
    def __init__(self, providers):
        self._providers = providers
        self._breakers = {name: CircuitBreaker() for name, _ in providers}

    def run(self):
        last_error = None
        for name, func in self._providers:
            breaker = self._breakers[name]
            if not breaker.can_attempt():
                logger.debug("Skipping %s: circuit %s", name, breaker.state.value)
                continue
            breaker.increment_half_open()
            try:
                result = func()
            except Exception as exc:
                breaker.record_failure()
                last_error = exc
                logger.warning("Provider %s failed: %s", name, exc)
                continue
            breaker.record_success()
            return name, result
        raise RuntimeError(f"All providers failed. Last error: {last_error}") from last_error


def retry_with_backoff(*, max_attempts=3, base_delay=1.0, max_delay=30.0, jitter=0.1, breaker=None, retryable_exceptions=(Exception,)):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(1, max_attempts + 1):
                if breaker is not None and not breaker.can_attempt():
                    raise RuntimeError(f"Circuit breaker open for {func.__name__}; skipping attempt")
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as exc:
                    last_exc = exc
                    if breaker is not None:
                        breaker.record_failure()
                    if attempt == max_attempts:
                        logger.error("%s failed after %d attempts: %s", func.__name__, max_attempts, exc)
                        raise
                    delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
                    if jitter > 0:
                        delay *= 1.0 + random.uniform(-jitter, jitter)
                    logger.warning("%s attempt %d/%d failed: %s — retrying in %.1fs", func.__name__, attempt, max_attempts, exc, delay)
                    time.sleep(delay)
            assert last_exc is not None
            raise last_exc
        return wrapper
    return decorator
