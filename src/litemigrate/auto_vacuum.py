def get_auto_vacuum_mode(conn):
    cursor = conn.execute("PRAGMA auto_vacuum;")
    row = cursor.fetchone()
    modes = {0: "NONE", 1: "FULL", 2: "INCREMENTAL"}
    return modes.get(row[0] if row else 0, "UNKNOWN")
