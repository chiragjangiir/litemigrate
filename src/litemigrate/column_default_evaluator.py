from typing import Optional

class ColumnDefaultEvaluator:
    @staticmethod
    def is_dynamic_default(default_expr: Optional[str]) -> bool:
        if not default_expr:
            return False
        upper = default_expr.upper().strip()
        return any(k in upper for k in ["CURRENT_TIMESTAMP", "CURRENT_DATE", "CURRENT_TIME", "DATETIME(", "STRFTIME("])
