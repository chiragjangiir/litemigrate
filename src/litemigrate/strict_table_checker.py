def is_strict_table(conn, table_name):
    cursor = conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name=?;", (table_name,))
    row = cursor.fetchone()
    if not row or not row[0]:
        return False
    return "STRICT" in row[0].upper().split(")")[-1]
