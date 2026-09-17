from __future__ import annotations

import time
from collections.abc import Callable
from typing import TypeVar

import httpx

from app.config import get_settings

T = TypeVar("T")

TRANSIENT_STATUS = {408, 425, 429, 500, 502, 503, 504}


def build_client(timeout: float | None = None) -> httpx.Client:
    settings = get_settings()
    return httpx.Client(
        timeout=timeout or settings.request_timeout_seconds,
        follow_redirects=False,
        headers={"User-Agent": settings.http_user_agent, "Accept": "text/html,application/json"},
    )


def retry_call(fn: Callable[[], T], attempts: int = 3, base_delay: float = 0.4) -> T:
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            return fn()
        except httpx.HTTPStatusError as exc:
            last_error = exc
            if exc.response.status_code not in TRANSIENT_STATUS:
                raise
        except (httpx.TimeoutException, httpx.NetworkError) as exc:
            last_error = exc
        if attempt < attempts - 1:
            time.sleep(base_delay * (2**attempt))
    assert last_error is not None
    raise last_error
