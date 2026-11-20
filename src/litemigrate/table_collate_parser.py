import re
from typing import Dict

class TableCollateParser:
    @classmethod
    def parse_collations(cls, ddl: str) -> Dict[str, str]:
        res = {}
        # match: identifier followed by type, then COLLATE <sequence>
        pattern = re.compile(r"(?:[(,]\s*|\n\s*)([a-zA-Z_]\w*)\s+[^,()]*?\bCOLLATE\s+([a-zA-Z_]\w*)", re.IGNORECASE)
        for match in pattern.finditer(ddl):
            col, collation = match.groups()
            res[col] = collation.upper()
        return res
