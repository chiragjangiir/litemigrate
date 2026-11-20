import sqlite3
from typing import List

class SqliteTransactionSavepointStack:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self.stack: List[str] = []

    def push(self, name: str):
        self.conn.execute(f"SAVEPOINT {name}")
        self.stack.append(name)

    def pop_commit(self):
        if not self.stack:
            return
        name = self.stack.pop()
        self.conn.execute(f"RELEASE SAVEPOINT {name}")

    def pop_rollback(self):
        if not self.stack:
            return
        name = self.stack.pop()
        self.conn.execute(f"ROLLBACK TO SAVEPOINT {name}")
        self.conn.execute(f"RELEASE SAVEPOINT {name}")
