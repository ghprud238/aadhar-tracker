"""
Circuit Breaker Pattern for External Intelligence Providers.
Protects the platform against cascading provider failures, aggressive 429 rate-limiting, and prolonged upstream outages.
"""
import time
import asyncio
from enum import Enum
from typing import Callable, Any, Optional


class CircuitState(str, Enum):
    CLOSED = "closed"        # Normal operations - queries flow to provider
    OPEN = "open"            # Tripped - fail-fast without calling provider
    HALF_OPEN = "half_open"  # Canary testing - allow single request to evaluate recovery


class CircuitBreakerOpenException(Exception):
    def __init__(self, provider_name: str, retry_after_seconds: float):
        self.provider_name = provider_name
        self.retry_after_seconds = retry_after_seconds
        super().__init__(
            f"Circuit breaker for provider '{provider_name}' is OPEN. "
            f"Retry allowed in {retry_after_seconds:.1f}s."
        )


class CircuitBreaker:
    def __init__(
        self,
        name: str,
        failure_threshold: int = 3,
        recovery_timeout_seconds: float = 30.0,
        half_open_success_threshold: int = 1
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout_seconds = recovery_timeout_seconds
        self.half_open_success_threshold = half_open_success_threshold

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None
        self.total_trips = 0
        self._lock = asyncio.Lock()

    def is_available(self) -> bool:
        """Returns True if requests are allowed to proceed."""
        if self.state == CircuitState.CLOSED:
            return True
        if self.state == CircuitState.OPEN:
            # Check if recovery timeout has elapsed
            if self.last_failure_time and (time.time() - self.last_failure_time >= self.recovery_timeout_seconds):
                return True
            return False
        # HALF_OPEN allows canaries
        return True

    def get_remaining_open_seconds(self) -> float:
        if self.state != CircuitState.OPEN or not self.last_failure_time:
            return 0.0
        elapsed = time.time() - self.last_failure_time
        return max(0.0, self.recovery_timeout_seconds - elapsed)

    async def record_success(self):
        async with self._lock:
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.half_open_success_threshold:
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
                    self.success_count = 0
            elif self.state == CircuitState.CLOSED:
                self.failure_count = 0

    async def record_failure(self):
        async with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            if self.state in (CircuitState.CLOSED, CircuitState.HALF_OPEN):
                if self.failure_count >= self.failure_threshold or self.state == CircuitState.HALF_OPEN:
                    self.state = CircuitState.OPEN
                    self.total_trips += 1
                    self.success_count = 0

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Executes the provider function protected by the circuit breaker."""
        async with self._lock:
            if self.state == CircuitState.OPEN:
                if self.last_failure_time and (time.time() - self.last_failure_time >= self.recovery_timeout_seconds):
                    self.state = CircuitState.HALF_OPEN
                    self.success_count = 0
                else:
                    raise CircuitBreakerOpenException(self.name, self.get_remaining_open_seconds())

        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            await self.record_success()
            return result
        except Exception:
            await self.record_failure()
            raise
