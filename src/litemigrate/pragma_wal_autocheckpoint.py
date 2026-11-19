import sqlite3

class PragmaWalAutocheckpoint:
    @staticmethod
    def get_checkpoint_pages(conn: sqlite3.Connection) -> int:
        return conn.execute("PRAGMA wal_autocheckpoint").fetchone()[0]

    @staticmethod
    def set_checkpoint_pages(conn: sqlite3.Connection, pages: int) -> int:
        return conn.execute(f"PRAGMA wal_autocheckpoint = {pages}").fetchone()[0]
