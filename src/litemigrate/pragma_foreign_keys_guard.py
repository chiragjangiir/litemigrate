import sqlite3
from contextlib import contextmanager

class PragmaForeignKeysGuard:
    @staticmethod
    @contextmanager
    def disabled(conn: sqlite3.Connection):
        orig = conn.execute("PRAGMA foreign_keys").fetchone()[0]
        conn.execute("PRAGMA foreign_keys = OFF")
        try:
            yield
        finally:
            conn.execute(f"PRAGMA foreign_keys = {orig}")
