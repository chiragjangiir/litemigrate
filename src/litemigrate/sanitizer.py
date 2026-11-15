"""SQL comment stripper and whitespace sanitizer."""
from __future__ import annotations
import re

def strip_sql_comments(sql: str) -> str:
    """Remove line comments (--) and block comments (/* */) from SQL."""
    # Remove block comments
    no_block = re.sub(r"/\*.*?\*/", "", sql, flags=re.DOTALL)
    # Remove single line comments
    lines = [re.sub(r"--.*?$", "", line) for line in no_block.splitlines()]
    return "\n".join(l for l in lines if l.strip())
