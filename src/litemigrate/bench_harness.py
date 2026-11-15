"""Automated benchmark harness for shadow migration profiling."""
from __future__ import annotations
import time
from typing import Callable, Any

def run_profiled_execution(name: str, fn: Callable[[], Any], iterations: int = 3) -> dict[str, Any]:
    times = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        fn()
        t1 = time.perf_counter()
        times.append((t1 - t0) * 1000.0)
    return {
        "benchmark": name,
        "iterations": iterations,
        "mean_ms": sum(times) / len(times),
        "min_ms": min(times),
        "max_ms": max(times),
    }
