def build_expression_index_sql(index_name, table_name, expression):
    return f"CREATE INDEX {index_name} ON {table_name} ({expression});"
