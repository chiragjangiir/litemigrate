def get_foreign_key_rules(conn, table_name):
    cursor = conn.execute(f"PRAGMA foreign_key_list({table_name});")
    rules = []
    for row in cursor.fetchall():
        rules.append({
            "target_table": row[2],
            "from_col": row[3],
            "to_col": row[4],
            "on_update": row[5],
            "on_delete": row[6]
        })
    return rules
