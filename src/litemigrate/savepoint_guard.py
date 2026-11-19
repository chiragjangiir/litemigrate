import sqlite3
from contextlib import contextmanager

class SavepointGuard:
    @staticmethod
    @contextmanager
    def guard(conn: sqlite3.Connection, name: str):
        conn.execute(f"SAVEPOINT {name}")
        try:
            yield
            conn.execute(f"RELEASE SAVEPOINT {name}")
        except Exception:
            conn.execute(f"ROLLBACK TO SAVEPOINT {name}")
            conn.execute(f"RELEASE SAVEPOINT {name}")
            raise
