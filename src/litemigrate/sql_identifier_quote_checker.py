class SqlIdentifierQuoteChecker:
    @staticmethod
    def is_quoted(name: str) -> bool:
        if not name or len(name) < 2:
            return False
        clean = name.strip()
        return (clean.startswith('"') and clean.endswith('"')) or \
               (clean.startswith('`') and clean.endswith('`')) or \
               (clean.startswith('[') and clean.endswith(']'))
