def is_json_valid_supported(conn):
    try:
        cursor = conn.execute("SELECT json_valid('{}');")
        row = cursor.fetchone()
        return bool(row and row[0] == 1)
    except Exception:
        return False
