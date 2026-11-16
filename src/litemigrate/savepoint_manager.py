"""Nested SQLite savepoint management."""
import sqlite3
import re
from contextlib import contextmanager

@contextmanager
def nested_savepoint(conn: sqlite3.Connection, name: str):
    if not re.match(r"^[A-Za-z0-9_]+$", name):
        raise ValueError(f"Invalid savepoint name: {name}")
    conn.execute(f"SAVEPOINT {name};")
    try:
        yield
        conn.execute(f"RELEASE SAVEPOINT {name};")
    except Exception:
        conn.execute(f"ROLLBACK TO SAVEPOINT {name};")
        conn.execute(f"RELEASE SAVEPOINT {name};")
        raise
