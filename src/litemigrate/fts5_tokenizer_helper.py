from typing import List, Optional

class Fts5TokenizerHelper:
    @staticmethod
    def build_tokenizer_clause(name: str, args: Optional[List[str]] = None) -> str:
        clean_name = name.strip()
        if not args:
            return f"tokenize = '{clean_name}'"
        joined = " ".join(arg.strip() for arg in args if arg.strip())
        return f"tokenize = '{clean_name} {joined}'"
