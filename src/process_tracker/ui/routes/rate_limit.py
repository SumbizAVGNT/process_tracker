# src/process_tracker/routes/rate_limit.py

from __future__ import annotations

import time
from collections import deque
from typing import Deque, Dict

from fastapi import HTTPException, Request, status

# Простейший leaky-bucket per-IP в памяти процесса.
# По-умолчанию: 60 запросов за 10 секунд.
WINDOW_SECONDS = 10.0
MAX_REQUESTS = 60

# ip -> deque[timestamps]
_BUCKETS: Dict[str, Deque[float]] = {}


def rate_limit(request: Request, max_requests: int = MAX_REQUESTS, window_seconds: float = WINDOW_SECONDS) -> None:
    """
    FastAPI dependency:
        @router.get("/...", dependencies=[Depends(rate_limit)])
    """
    ip = (request.client.host if request.client else "unknown") or "unknown"
    now = time.monotonic()

    q = _BUCKETS.get(ip)
    if q is None:
        q = deque()
        _BUCKETS[ip] = q

    # выкидываем старые метки
    cutoff = now - window_seconds
    while q and q[0] < cutoff:
        q.popleft()

    if len(q) >= max_requests:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests, slow down.",
        )

    q.append(now)
