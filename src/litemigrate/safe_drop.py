"""Safe table dropping utilities with foreign key cascade options."""
import re

def generate_safe_table_drop(table_name: str, cascade_foreign_keys: bool = False) -> str:
    if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", table_name):
        raise ValueError(f"Invalid table name: {table_name}")
    quoted = f'"{table_name}"'
    if cascade_foreign_keys:
        return f"PRAGMA foreign_keys = OFF;\nDROP TABLE IF EXISTS {quoted};\nPRAGMA foreign_keys = ON;"
    return f"DROP TABLE IF EXISTS {quoted};"
