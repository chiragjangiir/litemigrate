def read_blob_chunked(conn, table_name, column_name, rowid, chunk_size=4096):
    cursor = conn.execute(f"SELECT {column_name} FROM {table_name} WHERE rowid = ?;", (rowid,))
    row = cursor.fetchone()
    if not row or not row[0]:
        return
    data = row[0]
    for i in range(0, len(data), chunk_size):
        yield data[i:i + chunk_size]
