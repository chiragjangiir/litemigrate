import sqlite3

class SqliteVacuumAnalyzer:
    @staticmethod
    def should_vacuum(conn: sqlite3.Connection, fragmentation_threshold: float = 0.20) -> bool:
        cur = conn.cursor()
        page_count = cur.execute("PRAGMA page_count").fetchone()[0]
        freelist_count = cur.execute("PRAGMA freelist_count").fetchone()[0]
        if page_count == 0:
            return False
        ratio = freelist_count / float(page_count)
        return ratio >= fragmentation_threshold
