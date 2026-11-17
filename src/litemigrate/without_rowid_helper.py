def is_without_rowid(conn, table_name):
    cursor = conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name=?;", (table_name,))
    row = cursor.fetchone()
    if not row or not row[0]:
        return False
    return "WITHOUT ROWID" in row[0].upper()
