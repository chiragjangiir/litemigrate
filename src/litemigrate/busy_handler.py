def configure_busy_timeout(conn, timeout_ms=5000):
    timeout = max(0, int(timeout_ms))
    conn.execute(f"PRAGMA busy_timeout = {timeout};")
    cursor = conn.execute("PRAGMA busy_timeout;")
    row = cursor.fetchone()
    return row[0] if row else timeout
