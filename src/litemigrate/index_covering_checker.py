from typing import List, Set

class IndexCoveringChecker:
    @staticmethod
    def is_covering(indexed_columns: List[str], projected_columns: List[str]) -> bool:
        idx_set: Set[str] = {c.lower().strip() for c in indexed_columns}
        proj_set: Set[str] = {c.lower().strip() for c in projected_columns}
        return proj_set.issubset(idx_set)
