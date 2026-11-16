"""Standard SQLite collation sequence validator."""
STANDARD_COLLATIONS = {"BINARY", "NOCASE", "RTRIM"}

def is_valid_sqlite_collation(collation: str) -> bool:
    if not collation or not isinstance(collation, str):
        return False
    return collation.upper() in STANDARD_COLLATIONS
