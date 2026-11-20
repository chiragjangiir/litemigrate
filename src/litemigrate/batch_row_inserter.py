import sqlite3
from typing import List, Tuple, Any

class BatchRowInserter:
    @staticmethod
    def insert_in_batches(conn: sqlite3.Connection, sql: str, rows: List[Tuple[Any, ...]], batch_size: int = 500) -> int:
        cur = conn.cursor()
        total = 0
        for i in range(0, len(rows), batch_size):
            chunk = rows[i:i + batch_size]
            cur.executemany(sql, chunk)
            total += len(chunk)
        conn.commit()
        return total
