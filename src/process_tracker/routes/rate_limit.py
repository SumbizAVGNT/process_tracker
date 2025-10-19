from __future__ import annotations

import time
from collections import deque
from typing import Deque, Dict

from fastapi import HTTPException, Request, Response, status

# Простейший leaky-bucket per-IP в памяти процесса.
WINDOW_SECONDS = 10.0
MAX_REQUESTS = 60

# ip -> deque[timestamps]
_BUCKETS: Dict[str, Deque[float]] = {}


def rate_limit(
    request: Request,
    response: Response,
    max_requests: int = MAX_REQUESTS,
    window_seconds: float = WINDOW_SECONDS,
) -> None:
    """
    FastAPI dependency:
        @router.get("/...", dependencies=[Depends(rate_limit)])
    Добавляет заголовки:
      X-RateLimit-Limit / X-RateLimit-Remaining / X-RateLimit-Reset
    """
    ip = (request.client.host if request.client else "unknown") or "unknown"
    now = time.monotonic()

    q = _BUCKETS.get(ip)
    if q is None:
        q = deque()
        _BUCKETS[ip] = q

    cutoff = now - window_seconds
    while q and q[0] < cutoff:
        q.popleft()

    remaining_before = max(0, max_requests - len(q))
    if len(q) >= max_requests:
        reset_in = max(0.0, window_seconds - (now - q[0]))
        response.headers["X-RateLimit-Limit"] = str(max_requests)
        response.headers["X-RateLimit-Remaining"] = "0"
        response.headers["X-RateLimit-Reset"] = f"{reset_in:.3f}"
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests, slow down.",
        )

    q.append(now)
    reset_in = window_seconds if not q else max(0.0, window_seconds - (now - q[0]))
    response.headers["X-RateLimit-Limit"] = str(max_requests)
    response.headers["X-RateLimit-Remaining"] = str(max(0, remaining_before - 1))
    response.headers["X-RateLimit-Reset"] = f"{reset_in:.3f}"
