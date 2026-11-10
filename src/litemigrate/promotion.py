"""Atomic CAS promotion engine, writer leases, lockfiles, and rollback protection."""

from __future__ import annotations

import fcntl
import os
import sqlite3
import time
from collections.abc import Sequence
from pathlib import Path

from litemigrate.exceptions import (
    ConcurrencyConflictError,
    LockTimeoutError,
    UnsupportedMigrationTypeError,
)
from litemigrate.fingerprint import compute_logical_db_digest
from litemigrate.sqlite_backend import (
    bounded_sqlite_backup,
    open_hardened_sqlite,
    split_sql_statements,
)


def promote_shadow_to_source(
    shadow_path: Path,
    source_path: Path,
    *,
    expected_source_digest: str | None = None,
    migration_sql: str | Sequence[str] | None = None,
    disable_foreign_keys: bool = True,
    busy_timeout_ms: int = 3000,
    create_backup: bool = True,
) -> Path | None:
    """Safely promote the validated migration to `source_path` under an exclusive writer lease.

    1. Acquires an advisory POSIX flock on `<source_path>.litemigrate.lock`.
    2. Rejects unsupported callable migrations to maintain strict transaction atomicity.
    3. Creates a 0o600 rollback backup before making any modifications to `source_path`.
    4. Acquires BEGIN IMMEDIATE on `source_path`, blocking all external SQLite writers.
    5. Verifies live logical digest against `expected_source_digest` inside the held lock.
    6. Replays migration SQL statements inside the held transaction and commits atomically.
    """
    # Enforce Gap A: Reject callable migrations
    if callable(migration_sql):
        raise UnsupportedMigrationTypeError(
            "Arbitrary Python callable migrations are explicitly rejected by LiteMigrate for safety: "
            "they cannot be guaranteed atomic under SQLite transaction semantics and risk partial source corruption."
        )

    lock_file_path = Path(f"{source_path}.litemigrate.lock")
    lock_fd = os.open(
        str(lock_file_path),
        os.O_CREAT | os.O_RDWR | getattr(os, "O_NOFOLLOW", 0),
        0o600,
    )

    deadline = time.monotonic() + max(0.02, busy_timeout_ms / 1000.0)
    try:
        while True:
            try:
                fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    raise LockTimeoutError(
                        "database is locked (another LiteMigrate process holds exclusive promotion lock)"
                    )
                time.sleep(0.01)

        backup_path: Path | None = None
        if create_backup:
            timestamp_ns = time.time_ns()
            backup_path = Path(f"{source_path}.pre_migrate_{timestamp_ns}.bak")
            bounded_sqlite_backup(source_path, backup_path, busy_timeout_ms=busy_timeout_ms)

        if expected_source_digest is not None and migration_sql is not None:
            source_conn = open_hardened_sqlite(
                source_path,
                busy_timeout_ms=busy_timeout_ms,
                isolation_level=None,
            )
            try:
                fk_flag = 0 if disable_foreign_keys else 1
                source_conn.execute(f"PRAGMA foreign_keys = {fk_flag};")
                source_conn.execute("BEGIN IMMEDIATE;")
                try:
                    live_digest = compute_logical_db_digest(source_conn)

                    if live_digest != expected_source_digest:
                        source_conn.execute("ROLLBACK;")
                        raise ConcurrencyConflictError(
                            "Source database was modified by a concurrent writer prior to "
                            "promotion lock acquisition; aborting to prevent lost updates."
                        )

                    # Replay validated statements inside the held transaction
                    if isinstance(migration_sql, str):
                        statements = split_sql_statements(migration_sql)
                    else:
                        statements = []
                        for item in migration_sql:
                            statements.extend(split_sql_statements(item))

                    for stmt in statements:
                        source_conn.execute(stmt)

                    # Verify foreign keys and quick check before committing
                    fk_rows = source_conn.execute("PRAGMA foreign_key_check;").fetchall()
                    if fk_rows:
                        source_conn.execute("ROLLBACK;")
                        raise sqlite3.IntegrityError(
                            f"Foreign key constraint violation during promotion: {fk_rows}"
                        )

                    chk_rows = source_conn.execute("PRAGMA quick_check;").fetchall()
                    if chk_rows != [("ok",)]:
                        source_conn.execute("ROLLBACK;")
                        raise sqlite3.IntegrityError(
                            f"Database corruption detected during promotion quick_check: {chk_rows}"
                        )

                    source_conn.execute("COMMIT;")
                except Exception:
                    if source_conn.in_transaction:
                        try:
                            source_conn.execute("ROLLBACK;")
                        except sqlite3.Error:
                            pass
                    raise
                finally:
                    try:
                        source_conn.execute("PRAGMA foreign_keys = ON;")
                    except sqlite3.Error:
                        pass
            finally:
                source_conn.close()
        else:
            # Fallback direct page backup for cases where no SQL statements were provided
            bounded_sqlite_backup(shadow_path, source_path, busy_timeout_ms=busy_timeout_ms)

        return backup_path
    finally:
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
        except OSError:
            pass
        os.close(lock_fd)
        try:
            lock_file_path.unlink()
        except OSError:
            pass
