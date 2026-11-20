import re
from typing import Dict, List, Set

class ViewDependencyGraph:
    @staticmethod
    def extract_dependencies(view_sql: str, known_tables: Set[str]) -> List[str]:
        deps = []
        for tbl in known_tables:
            pattern = rf"\b{re.escape(tbl)}\b"
            if re.search(pattern, view_sql, re.IGNORECASE):
                deps.append(tbl)
        return sorted(deps)
