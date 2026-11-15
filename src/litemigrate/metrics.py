"""
Performance measurement and telemetry helpers for shadow validation.
"""

from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass
class ExecutionTimer:
    start_time: float = 0.0
    end_time: float = 0.0

    def start(self) -> ExecutionTimer:
        self.start_time = time.perf_counter()
        return self

    def stop(self) -> float:
        self.end_time = time.perf_counter()
        return self.elapsed_ms

    @property
    def elapsed_ms(self) -> float:
        return (self.end_time - self.start_time) * 1000.0


def calculate_throughput_rows_per_sec(row_count: int, elapsed_ms: float) -> float:
    if elapsed_ms <= 0.0 or row_count <= 0:
        return 0.0
    return (row_count / elapsed_ms) * 1000.0
