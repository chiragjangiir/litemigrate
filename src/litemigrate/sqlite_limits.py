def get_max_page_count(conn):
    cursor = conn.execute("PRAGMA max_page_count;")
    row = cursor.fetchone()
    return row[0] if row else 1073741823
