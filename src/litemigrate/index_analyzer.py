"""Index usage and coverage analyzer for SQLite schemas."""
from __future__ import annotations
import sqlite3

def analyze_table_indexes(conn: sqlite3.Connection, table_name: str) -> list[str]:
    cursor = conn.cursor()
    try:
        cursor.execute(f"PRAGMA index_list({table_name});")
        return [row[1] for row in cursor.fetchall()]
    finally:
        cursor.close()
