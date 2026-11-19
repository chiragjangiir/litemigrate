import sqlite3
from typing import List

class BatchStatementRunner:
    @staticmethod
    def execute_script(conn: sqlite3.Connection, statements: List[str]) -> int:
        cur = conn.cursor()
        count = 0
        for stmt in statements:
            clean = stmt.strip()
            if clean:
                cur.execute(clean)
                count += 1
        conn.commit()
        return count
