def get_page_size(conn):
    cursor = conn.execute("PRAGMA page_size;")
    row = cursor.fetchone()
    return row[0] if row else 4096
