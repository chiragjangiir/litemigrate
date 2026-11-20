import sqlite3
import io

class InMemoryDbSnapshot:
    @staticmethod
    def snapshot_to_sql(conn: sqlite3.Connection) -> str:
        buffer = io.StringIO()
        for line in conn.iterdump():
            buffer.write(f"{line}\n")
        return buffer.getvalue()
