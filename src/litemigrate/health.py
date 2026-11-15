"""Database health and integrity verification helpers."""
from __future__ import annotations
import sqlite3

def check_database_health(conn: sqlite3.Connection) -> tuple[bool, str]:
    cursor = conn.cursor()
    try:
        cursor.execute("PRAGMA quick_check;")
        row = cursor.fetchone()
        if row and row[0] == "ok":
            return True, "ok"
        return False, str(row[0]) if row else "unknown failure"
    finally:
        cursor.close()
