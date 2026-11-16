"""Table rewrite generator for complex SQLite column migrations."""
from typing import List

def generate_temp_table_migration_sql(table_name: str, common_columns: List[str]) -> str:
    cols = ", ".join(f'"{c}"' for c in common_columns)
    temp_name = f'"{table_name}__old_backup"'
    target = f'"{table_name}"'
    return f"""ALTER TABLE {target} RENAME TO {temp_name};
INSERT INTO {target} ({cols}) SELECT {cols} FROM {temp_name};
DROP TABLE {temp_name};"""
