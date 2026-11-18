import re

def extract_view_referenced_tables(view_sql):
    matches = re.findall(r"\bFROM\s+([a-zA-Z0-9_]+)|\bJOIN\s+([a-zA-Z0-9_]+)", view_sql, re.IGNORECASE)
    tables = set()
    for m in matches:
        tables.add(m[0] if m[0] else m[1])
    return sorted(list(tables))
