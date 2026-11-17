def list_triggers(conn):
    cursor = conn.execute("SELECT name, tbl_name, sql FROM sqlite_master WHERE type='trigger' ORDER BY name;")
    return [{"name": row[0], "table": row[1], "sql": row[2]} for row in cursor.fetchall()]
