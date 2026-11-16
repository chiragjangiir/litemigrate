"""Schema column difference calculator."""
from typing import List, Dict, Any

def compute_column_alteration_diff(cols_before: List[str], cols_after: List[str]) -> Dict[str, List[str]]:
    set_b = set(cols_before)
    set_a = set(cols_after)
    return {
        "added": [c for c in cols_after if c not in set_b],
        "removed": [c for c in cols_before if c not in set_a],
        "retained": [c for c in cols_before if c in set_a]
    }
