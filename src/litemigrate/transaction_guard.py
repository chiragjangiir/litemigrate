"""Context manager for atomic SQLite migration execution."""
import sqlite3
from contextlib import contextmanager

@contextmanager
def transactional_migration_scope(conn: sqlite3.Connection):
    try:
        conn.execute("BEGIN IMMEDIATE;")
        yield conn
        conn.execute("COMMIT;")
    except Exception:
        conn.execute("ROLLBACK;")
        raise
