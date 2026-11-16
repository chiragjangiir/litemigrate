"""Execute SQL scripts statement-by-statement with progress reporting."""
import sqlite3
from typing import Callable, Optional

def execute_script_with_progress(conn: sqlite3.Connection, script: str, progress_fn: Optional[Callable[[int, int], None]] = None) -> int:
    stmts = [s.strip() for s in script.split(";") if s.strip()]
    total = len(stmts)
    for idx, stmt in enumerate(stmts, 1):
        conn.execute(stmt)
        if progress_fn:
            progress_fn(idx, total)
    return total
