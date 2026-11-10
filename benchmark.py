"""Reproducible benchmark suite for LiteMigrate clone strategies, memory RSS, and audit latency."""

from __future__ import annotations

import os
import resource
import sqlite3
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from litemigrate.cloning import create_shadow_database
from litemigrate.engine import LiteMigrateEngine
from litemigrate.models import CloneStrategy
from tests.fixtures.database_setup import create_test_database, populate_to_target_size_mb


def measure_isolated_task(target_func_name: str, db_path_str: str, strategy_str: str) -> None:
    """Subprocess target measuring isolated peak RSS and execution time."""
    db_path = Path(db_path_str)
    strategy = CloneStrategy(strategy_str)

    t0 = time.perf_counter()
    if target_func_name == "clone":
        res = create_shadow_database(db_path, strategy=strategy)
        elapsed = (time.perf_counter() - t0) * 1000.0
        res.shadow_path.unlink()
        try:
            res.shadow_path.parent.rmdir()
        except OSError:
            pass
    elif target_func_name == "validate":
        report = LiteMigrateEngine.execute_and_validate(
            source_db=db_path,
            migration_sql="ALTER TABLE parent_table ADD COLUMN benchmark_test TEXT;",
            clone_strategy=strategy,
        )
        elapsed = (time.perf_counter() - t0) * 1000.0

    # Report peak RSS
    ru = resource.getrusage(resource.RUSAGE_SELF)
    # ru_maxrss is bytes on macOS Darwin, kilobytes on Linux
    peak_rss_mb = (
        ru.ru_maxrss / (1024.0 * 1024.0)
        if sys.platform == "darwin"
        else ru.ru_maxrss / 1024.0
    )
    print(f"RESULT|{elapsed:.3f}|{peak_rss_mb:.2f}")


def run_benchmark_scale(target_mb: float) -> dict[str, float]:
    with tempfile.TemporaryDirectory() as td:
        db_path = Path(td) / f"bench_{int(target_mb)}mb.db"
        print(f"\n--- Benchmarking Scale: {target_mb} MB ({db_path.name}) ---")
        create_test_database(db_path)
        populate_to_target_size_mb(db_path, target_mb)
        actual_size_mb = db_path.stat().st_size / (1024.0 * 1024.0)
        print(f"Database populated: {actual_size_mb:.2f} MB on disk.")

        strategies = [CloneStrategy.SQLITE_BACKUP_API]
        if sys.platform == "darwin":
            strategies.insert(0, CloneStrategy.APFS_CLONEFILE)
        elif sys.platform.startswith("linux"):
            strategies.insert(0, CloneStrategy.LINUX_FICLONE)

        results: dict[str, float] = {"actual_size_mb": actual_size_mb}

        for strat in strategies:
            # 1. Benchmark isolated Clone
            cmd_clone = [
                sys.executable,
                "-c",
                f"from benchmark import measure_isolated_task; measure_isolated_task('clone', {repr(str(db_path))}, {repr(strat.value)})",
            ]
            out_c = subprocess.check_output(cmd_clone, text=True, cwd=str(Path(__file__).parent)).strip()
            _, dur_c, rss_c = out_c.split("|")
            print(f"[{strat.value}] Clone:    {float(dur_c):.2f} ms | Peak RSS: {float(rss_c):.2f} MB")
            results[f"{strat.value}_clone_ms"] = float(dur_c)
            results[f"{strat.value}_clone_rss_mb"] = float(rss_c)

            # 2. Benchmark isolated Validate
            cmd_val = [
                sys.executable,
                "-c",
                f"from benchmark import measure_isolated_task; measure_isolated_task('validate', {repr(str(db_path))}, {repr(strat.value)})",
            ]
            out_v = subprocess.check_output(cmd_val, text=True, cwd=str(Path(__file__).parent)).strip()
            _, dur_v, rss_v = out_v.split("|")
            print(f"[{strat.value}] Validate: {float(dur_v):.2f} ms | Peak RSS: {float(rss_v):.2f} MB")
            results[f"{strat.value}_validate_ms"] = float(dur_v)
            results[f"{strat.value}_validate_rss_mb"] = float(rss_v)

        return results


def main() -> None:
    print("=================================================================")
    print(" LiteMigrate — Performance & Isolated Peak RSS Benchmark")
    print("=================================================================")
    print(f"Platform: {sys.platform} | Python: {sys.version.split()[0]} | SQLite: {sqlite3.sqlite_version}")

    scales = [5.0, 25.0]
    for scale in scales:
        run_benchmark_scale(scale)
    print("\nBenchmark completed successfully.")


if __name__ == "__main__":
    main()
