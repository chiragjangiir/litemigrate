"""Normalized SQLite DDL dumper for git-diff tracking."""
import sqlite3

def dump_schema_sql_normalized(conn: sqlite3.Connection) -> str:
    cur = conn.cursor()
    rows = cur.execute(
        "SELECT sql FROM sqlite_master WHERE sql IS NOT NULL AND name NOT LIKE 'sqlite_%' ORDER BY type, name;"
    ).fetchall()
    ddl_lines = [r[0].strip() + ";" for r in rows if r[0]]
    return "\n\n".join(ddl_lines)
