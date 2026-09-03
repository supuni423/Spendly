import time
from collections import defaultdict

from fastapi import HTTPException, Request, status

# In-memory, per-process fixed-window limiter. Sufficient for a
# single-instance deployment; a multi-instance production deployment would
# need a shared store (e.g. Redis) instead — noted here rather than silently
# assumed.
_buckets: dict[str, list[float]] = defaultdict(list)


def _client_key(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def rate_limit(name: str, max_requests: int, window_seconds: int = 60):
    """FastAPI dependency factory. Limits each client IP to `max_requests`
    within a rolling `window_seconds` window, scoped by `name` so different
    endpoints don't share a budget.
    """

    def dependency(request: Request) -> None:
        key = f"{name}:{_client_key(request)}"
        now = time.monotonic()
        window_start = now - window_seconds

        bucket = _buckets[key]
        while bucket and bucket[0] < window_start:
            bucket.pop(0)

        if len(bucket) >= max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please slow down and try again shortly.",
            )

        bucket.append(now)

    return dependency
