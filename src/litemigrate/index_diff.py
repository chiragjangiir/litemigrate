"""Index coverage verification for foreign key columns."""
import sqlite3
from typing import List, Dict, Any

def detect_missing_indexes_for_foreign_keys(conn: sqlite3.Connection, table_name: str) -> List[Dict[str, Any]]:
    cur = conn.cursor()
    fks = cur.execute(f'PRAGMA foreign_key_list("{table_name}");').fetchall()
    indices = cur.execute(f'PRAGMA index_list("{table_name}");').fetchall()
    indexed_cols = set()
    for idx in indices:
        idx_name = idx[1]
        for col_info in cur.execute(f'PRAGMA index_info("{idx_name}");').fetchall():
            indexed_cols.add(col_info[2])
    
    missing = []
    for fk in fks:
        from_col = fk[3]
        if from_col not in indexed_cols:
            missing.append({"table": table_name, "column": from_col, "ref_table": fk[2], "ref_col": fk[4]})
    return missing
