"""Foreign key constraint violation checker."""
import sqlite3
from typing import List, Dict, Any

def check_foreign_key_violations(conn: sqlite3.Connection, table_name: str = "") -> List[Dict[str, Any]]:
    cur = conn.cursor()
    query = f'PRAGMA foreign_key_check("{table_name}");' if table_name else "PRAGMA foreign_key_check;"
    rows = cur.execute(query).fetchall()
    violations = []
    for r in rows:
        violations.append({
            "table": r[0],
            "rowid": r[1],
            "target": r[2],
            "fkid": r[3]
        })
    return violations
