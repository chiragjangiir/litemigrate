def build_upsert_sql(table_name, key_cols, update_cols):
    all_cols = key_cols + update_cols
    col_str = ", ".join(all_cols)
    placeholders = ", ".join(["?"] * len(all_cols))
    conflict_keys = ", ".join(key_cols)
    set_clause = ", ".join([f"{c} = excluded.{c}" for c in update_cols])
    return f"INSERT INTO {table_name} ({col_str}) VALUES ({placeholders}) ON CONFLICT ({conflict_keys}) DO UPDATE SET {set_clause};"
