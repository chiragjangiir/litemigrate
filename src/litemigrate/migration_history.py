def init_history_table(conn):
    conn.execute("""
    CREATE TABLE IF NOT EXISTS _litemigrate_history (
        version TEXT PRIMARY KEY,
        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        checksum TEXT NOT NULL
    );
    """)
    return True

def record_migration(conn, version, checksum):
    conn.execute("INSERT OR REPLACE INTO _litemigrate_history (version, checksum) VALUES (?, ?);", (version, checksum))
