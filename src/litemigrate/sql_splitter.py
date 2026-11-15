"""SQL statement splitting helper respecting quotes, comments and semicolons."""
from __future__ import annotations
import re

def split_sql_statements(sql: str) -> list[str]:
    """Split raw SQL string into distinct executable statements."""
    statements: list[str] = []
    current: list[str] = []
    in_single_quote = False
    in_double_quote = False

    for char in sql:
        if char == "'" and not in_double_quote:
            in_single_quote = not in_single_quote
            current.append(char)
        elif char == '"' and not in_single_quote:
            in_double_quote = not in_double_quote
            current.append(char)
        elif char == ';' and not in_single_quote and not in_double_quote:
            stmt = "".join(current).strip()
            if stmt:
                statements.append(stmt)
            current = []
        else:
            current.append(char)

    last = "".join(current).strip()
    if last:
        statements.append(last)
    return statements
