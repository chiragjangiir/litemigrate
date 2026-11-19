import sqlite3
import threading
from typing import Dict

class InMemoryConnectionPool:
    def __init__(self):
        self._pool: Dict[str, sqlite3.Connection] = {}
        self._lock = threading.Lock()

    def get_shared_memory_connection(self, db_name: str) -> sqlite3.Connection:
        with self._lock:
            uri = f"file:{db_name}?mode=memory&cache=shared"
            conn = sqlite3.connect(uri, uri=True, check_same_thread=False)
            return conn
