def get_available_collations(conn):
    cursor = conn.execute("PRAGMA collation_list;")
    return [row[1] for row in cursor.fetchall()]
