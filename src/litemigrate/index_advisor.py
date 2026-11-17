def suggest_index_name(table_name, columns):
    col_part = "_".join(columns)
    return f"idx_{table_name}_{col_part}"
