def configure_temp_store_memory(conn):
    conn.execute("PRAGMA temp_store = MEMORY;")
    cursor = conn.execute("PRAGMA temp_store;")
    row = cursor.fetchone()
    return row[0] if row else 2
