"""Retry utility with exponential backoff for lock contention."""
from __future__ import annotations
import time
from typing import Callable, TypeVar

T = TypeVar("T")

def retry_with_backoff(
    action: Callable[[], T],
    max_attempts: int = 5,
    initial_delay: float = 0.05,
    multiplier: float = 2.0,
) -> T:
    delay = initial_delay
    last_err: Exception | None = None
    for attempt in range(max_attempts):
        try:
            return action()
        except Exception as e:
            last_err = e
            if attempt == max_attempts - 1:
                break
            time.sleep(delay)
            delay *= multiplier
    raise last_err or RuntimeError("Retry attempts exhausted")
