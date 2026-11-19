from typing import List

class TableColumnOrderDiff:
    @staticmethod
    def order_matches(cols_a: List[str], cols_b: List[str]) -> bool:
        clean_a = [c.lower().strip() for c in cols_a]
        clean_b = [c.lower().strip() for c in cols_b]
        return clean_a == clean_b
