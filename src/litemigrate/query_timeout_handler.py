import sqlite3
import time

class QueryTimeoutHandler:
    @staticmethod
    def set_timeout(conn: sqlite3.Connection, timeout_seconds: float):
        deadline = time.time() + timeout_seconds

        def handler():
            if time.time() > deadline:
                return 1
            return 0

        conn.set_progress_handler(handler, 1000)

    @staticmethod
    def clear_timeout(conn: sqlite3.Connection):
        conn.set_progress_handler(None, 0)
