def get_cache_size(conn):
    cursor = conn.execute("PRAGMA cache_size;")
    row = cursor.fetchone()
    return row[0] if row else -2000
