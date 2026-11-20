import sqlite3

class SchemaVersionGuard:
    @staticmethod
    def verify_and_increment(conn: sqlite3.Connection, expected_version: int) -> int:
        cur = conn.cursor()
        current = cur.execute("PRAGMA user_version").fetchone()[0]
        if current != expected_version:
            raise ValueError(f"Version mismatch: expected {expected_version}, got {current}")
        new_version = current + 1
        cur.execute(f"PRAGMA user_version = {new_version}")
        return new_version
