import hashlib
import sqlite3

class TableRowHasher:
    @staticmethod
    def hash_rows(conn: sqlite3.Connection, table_name: str, order_by: str) -> str:
        hasher = hashlib.sha256()
        cursor = conn.cursor()
        cursor.execute(f'SELECT * FROM "{table_name}" ORDER BY {order_by}')
        for row in cursor.fetchall():
            row_str = "|".join("" if v is None else str(v) for v in row)
            hasher.update(row_str.encode("utf-8"))
        return hasher.hexdigest()
