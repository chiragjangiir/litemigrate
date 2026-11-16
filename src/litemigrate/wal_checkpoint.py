"""WAL auto-checkpoint and truncation utility."""
import sqlite3
from typing import Dict, Any

def wal_checkpoint_truncate(conn: sqlite3.Connection) -> Dict[str, Any]:
    cur = conn.cursor()
    row = cur.execute("PRAGMA wal_checkpoint(TRUNCATE);").fetchone()
    if row:
        return {"busy": bool(row[0]), "log_pages": int(row[1]), "checkpointed_pages": int(row[2])}
    return {"busy": False, "log_pages": 0, "checkpointed_pages": 0}
