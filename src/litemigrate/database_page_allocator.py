import sqlite3
from typing import Dict

class DatabasePageAllocator:
    @staticmethod
    def get_allocation_stats(conn: sqlite3.Connection) -> Dict[str, int]:
        cur = conn.cursor()
        page_size = cur.execute("PRAGMA page_size").fetchone()[0]
        page_count = cur.execute("PRAGMA page_count").fetchone()[0]
        freelist_count = cur.execute("PRAGMA freelist_count").fetchone()[0]
        total_bytes = page_size * page_count
        free_bytes = page_size * freelist_count
        return {
            "page_size": page_size,
            "page_count": page_count,
            "freelist_count": freelist_count,
            "total_bytes": total_bytes,
            "free_bytes": free_bytes
        }
