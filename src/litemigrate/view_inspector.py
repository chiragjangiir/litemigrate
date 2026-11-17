def list_views(conn):
    cursor = conn.execute("SELECT name, sql FROM sqlite_master WHERE type='view' ORDER BY name;")
    return [{"name": row[0], "sql": row[1]} for row in cursor.fetchall()]
