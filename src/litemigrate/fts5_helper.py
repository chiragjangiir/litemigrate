def generate_fts5_ddl(table_name, columns):
    cols = ", ".join(columns)
    return f"CREATE VIRTUAL TABLE {table_name} USING fts5({cols});"
