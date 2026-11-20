class PartialIndexPredicateValidator:
    @staticmethod
    def is_valid_where_clause(where_expr: str) -> bool:
        if not where_expr or not where_expr.strip():
            return False
        clean = where_expr.strip()
        # Disallow unbalanced parentheses or semicolon injection
        if clean.count("(") != clean.count(")"):
            return False
        if ";" in clean:
            return False
        return True
