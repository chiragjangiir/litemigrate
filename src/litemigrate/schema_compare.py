def get_table_names(conn):
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name;")
    return [row[0] for row in cursor.fetchall()]

def compare_tables(conn1, conn2):
    t1 = set(get_table_names(conn1))
    t2 = set(get_table_names(conn2))
    return {
        "added": sorted(list(t2 - t1)),
        "removed": sorted(list(t1 - t2)),
        "common": sorted(list(t1 & t2))
    }
