"""Test database fixtures and schema population helpers."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from litemigrate.sqlite_backend import enforce_untrusted_schema, open_hardened_sqlite


def create_test_database(db_path: Path | str, *, enable_wal: bool = False) -> sqlite3.Connection:
    """Create a standardized test database with parent/child tables and foreign key cascade."""
    p = Path(db_path)
    if p.exists():
        p.unlink()

    conn = open_hardened_sqlite(p, busy_timeout_ms=5000)
    enforce_untrusted_schema(conn)

    if enable_wal:
        conn.execute("PRAGMA journal_mode = WAL;")

    conn.execute(
        """
        CREATE TABLE parent_table (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT
        );
        """
    )
    conn.execute(
        """
        CREATE TABLE child_table (
            id INTEGER PRIMARY KEY,
            parent_id INTEGER NOT NULL,
            amount_cents INTEGER NOT NULL,
            FOREIGN KEY (parent_id) REFERENCES parent_table(id) ON DELETE CASCADE
        );
        """
    )
    conn.execute("CREATE INDEX idx_child_parent ON child_table(parent_id);")

    # Insert default baseline records
    conn.execute("INSERT INTO parent_table VALUES (1, 'Parent One', 'Original description');")
    conn.execute("INSERT INTO parent_table VALUES (2, 'Parent Two', 'Second description');")

    for i in range(1, 21):
        conn.execute(
            f"INSERT INTO child_table VALUES ({i}, 1, {i * 100});"
        )
    for i in range(21, 41):
        conn.execute(
            f"INSERT INTO child_table VALUES ({i}, 2, {i * 200});"
        )

    conn.commit()
    return conn


def populate_to_target_size_mb(
    db_path: Path | str, target_size_mb: float, batch_size: int = 2000
) -> int:
    """Populate test database with rows until it reaches target size in megabytes."""
    conn = open_hardened_sqlite(db_path, busy_timeout_ms=5000)
    target_bytes = int(target_size_mb * 1024 * 1024)

    cur_id = 1000
    rows_added = 0

    while Path(db_path).stat().st_size < target_bytes:
        conn.execute("BEGIN TRANSACTION;")
        for _ in range(batch_size):
            cur_id += 1
            conn.execute(
                f"INSERT INTO child_table (id, parent_id, amount_cents) VALUES ({cur_id}, 1, {cur_id});"
            )
            rows_added += 1
        conn.commit()

    conn.close()
    return rows_added
