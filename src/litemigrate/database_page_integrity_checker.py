import sqlite3
from typing import List

class DatabasePageIntegrityChecker:
    @staticmethod
    def check_integrity(conn: sqlite3.Connection, max_errors: int = 100) -> List[str]:
        cur = conn.cursor()
        rows = cur.execute(f"PRAGMA integrity_check({max_errors})").fetchall()
        return [r[0] for r in rows]
