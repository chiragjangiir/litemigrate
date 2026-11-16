"""SQLite VACUUM INTO safe destination file creator."""
import sqlite3
from pathlib import Path

def safe_vacuum_into(conn: sqlite3.Connection, destination_path: str) -> bool:
    dest = Path(destination_path)
    if dest.exists():
        raise FileExistsError(f"Destination already exists: {destination_path}")
    old_iso = conn.isolation_level
    try:
        conn.commit()
        conn.isolation_level = None
        conn.execute(f"VACUUM INTO '{dest.as_posix()}';")
    finally:
        conn.isolation_level = old_iso
    return dest.exists()
