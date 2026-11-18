def quote_identifier(identifier):
    if not identifier:
        raise ValueError("Identifier cannot be empty")
    escaped = identifier.replace('"', '""')
    return f'"{escaped}"'
