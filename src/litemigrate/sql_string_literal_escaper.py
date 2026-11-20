class SqlStringLiteralEscaper:
    @staticmethod
    def escape_literal(val: str) -> str:
        if val is None:
            return "NULL"
        escaped = val.replace("'", "''")
        return f"'{escaped}'"
