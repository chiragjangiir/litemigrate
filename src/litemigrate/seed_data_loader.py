def bulk_insert(conn, table_name, records):
    if not records:
        return 0
    columns = list(records[0].keys())
    col_str = ", ".join(columns)
    placeholders = ", ".join(["?"] * len(columns))
    sql = f"INSERT INTO {table_name} ({col_str}) VALUES ({placeholders});"
    params = [[r[c] for c in columns] for r in records]
    cursor = conn.executemany(sql, params)
    return cursor.rowcount
