def build_partial_index_sql(index_name, table_name, columns, where_clause):
    cols = ", ".join(columns)
    return f"CREATE INDEX {index_name} ON {table_name} ({cols}) WHERE {where_clause};"
