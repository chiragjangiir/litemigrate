def estimate_table_rows(conn, table_name):
    try:
        cursor = conn.execute(f"SELECT max(_rowid_) FROM {table_name};")
        row = cursor.fetchone()
        return row[0] if row and row[0] is not None else 0
    except Exception:
        cursor = conn.execute(f"SELECT count(*) FROM {table_name};")
        return cursor.fetchone()[0]
