from __future__ import annotations

import threading
import time
from collections import defaultdict, deque


class SlidingWindowRateLimiter:
    def __init__(self) -> None:
        self._events: dict[tuple[str, str], deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(
        self,
        *,
        bucket: str,
        identity: str,
        limit: int,
        window_seconds: int,
        now: float | None = None,
    ) -> bool:
        current = time.monotonic() if now is None else now
        cutoff = current - window_seconds
        key = (bucket, identity)

        with self._lock:
            events = self._events[key]
            while events and events[0] <= cutoff:
                events.popleft()
            if len(events) >= limit:
                return False
            events.append(current)

            # Opportunistic cleanup keeps the dictionary bounded on a
            # long-running single-process storefront.
            if len(self._events) > 10_000:
                stale_keys = [
                    candidate
                    for candidate, values in self._events.items()
                    if not values or values[-1] <= cutoff
                ][:1000]
                for candidate in stale_keys:
                    self._events.pop(candidate, None)

        return True


limiter = SlidingWindowRateLimiter()
