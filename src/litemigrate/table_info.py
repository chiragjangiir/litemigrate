"""SQLite table xinfo parsing utilities."""
import sqlite3
from typing import List, Dict, Any

def parse_pragma_table_info_extended(conn: sqlite3.Connection, table_name: str) -> List[Dict[str, Any]]:
    cur = conn.cursor()
    rows = cur.execute(f'PRAGMA table_xinfo("{table_name}");').fetchall()
    cols = []
    for r in rows:
        cols.append({
            "cid": r[0],
            "name": r[1],
            "type": r[2],
            "notnull": bool(r[3]),
            "dflt_value": r[4],
            "pk": int(r[5]),
            "hidden": int(r[6]) if len(r) > 6 else 0
        })
    return cols
