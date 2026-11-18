def get_journal_mode(conn):
    cursor = conn.execute("PRAGMA journal_mode;")
    row = cursor.fetchone()
    return row[0].upper() if row else "DELETE"
