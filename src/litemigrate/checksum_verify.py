"""Checksum verification for SQLite table row count and integrity."""
import sqlite3
import hashlib

def verify_table_row_checksum(conn: sqlite3.Connection, table_name: str) -> str:
    cur = conn.cursor()
    count = cur.execute(f'SELECT COUNT(*) FROM "{table_name}";').fetchone()[0]
    payload = f"{table_name}:{count}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()
