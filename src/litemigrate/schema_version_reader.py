def get_user_version(conn):
    cursor = conn.execute("PRAGMA user_version;")
    row = cursor.fetchone()
    return row[0] if row else 0

def set_user_version(conn, version):
    v = max(0, int(version))
    conn.execute(f"PRAGMA user_version = {v};")
