import sqlite3
from typing import Tuple

class TableRowComparator:
    @staticmethod
    def compare_counts(conn: sqlite3.Connection, table_a: str, table_b: str) -> Tuple[int, int, bool]:
        cur = conn.cursor()
        cnt_a = cur.execute(f'SELECT COUNT(*) FROM "{table_a}"').fetchone()[0]
        cnt_b = cur.execute(f'SELECT COUNT(*) FROM "{table_b}"').fetchone()[0]
        return cnt_a, cnt_b, cnt_a == cnt_b
