def get_freelist_count(conn):
    cursor = conn.execute("PRAGMA freelist_count;")
    row = cursor.fetchone()
    return row[0] if row else 0
