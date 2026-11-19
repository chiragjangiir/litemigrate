import sqlite3
import time

class SchemaMigrationLock:
    LOCK_TABLE = "_litemigrate_lock"

    @staticmethod
    def init_lock_table(conn: sqlite3.Connection):
        conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {SchemaMigrationLock.LOCK_TABLE} (
                id INTEGER PRIMARY KEY,
                locked_at INTEGER,
                owner TEXT
            )
        """)
        conn.commit()

    @staticmethod
    def acquire(conn: sqlite3.Connection, owner: str) -> bool:
        SchemaMigrationLock.init_lock_table(conn)
        now = int(time.time())
        try:
            conn.execute(f"INSERT INTO {SchemaMigrationLock.LOCK_TABLE} (id, locked_at, owner) VALUES (1, ?, ?)", (now, owner))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    @staticmethod
    def release(conn: sqlite3.Connection):
        conn.execute(f"DELETE FROM {SchemaMigrationLock.LOCK_TABLE} WHERE id = 1")
        conn.commit()
