import sqlite3

class PragmaRecursiveTriggers:
    @staticmethod
    def get_status(conn: sqlite3.Connection) -> bool:
        val = conn.execute("PRAGMA recursive_triggers").fetchone()[0]
        return bool(val)

    @staticmethod
    def set_status(conn: sqlite3.Connection, enabled: bool):
        val = 1 if enabled else 0
        conn.execute(f"PRAGMA recursive_triggers = {val}")
