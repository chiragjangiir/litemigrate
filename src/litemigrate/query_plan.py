"""Explain Query Plan utilities for migration verification."""
import sqlite3
from typing import List, Dict, Any

def explain_query_plan(conn: sqlite3.Connection, query: str) -> List[Dict[str, Any]]:
    cur = conn.cursor()
    rows = cur.execute(f"EXPLAIN QUERY PLAN {query};").fetchall()
    return [{"id": r[0], "parent": r[1], "detail": r[3] if len(r) > 3 else r[2]} for r in rows]
