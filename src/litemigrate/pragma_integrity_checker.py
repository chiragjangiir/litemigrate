def check_database_integrity_fast(conn):
    cursor = conn.execute("PRAGMA quick_check;")
    row = cursor.fetchone()
    return bool(row and row[0] == "ok")
