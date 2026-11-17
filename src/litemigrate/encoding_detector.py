def get_database_encoding(conn):
    cursor = conn.execute("PRAGMA encoding;")
    row = cursor.fetchone()
    return row[0] if row else "UTF-8"
