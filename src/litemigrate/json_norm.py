"""
JSON normalization utilities for SQLite schema and data verification.
Canonicalizes JSON objects and arrays to ensure deterministic string representations.
"""

from __future__ import annotations

import json
from typing import Any


def canonicalize_json(raw: str | bytes | None) -> str | None:
    """
    Parse a JSON string or bytes and return its canonical string representation
    with sorted keys, no whitespace around delimiters, and UTF-8 encoding.
    Returns None if input is None, or returns the original string if not valid JSON.
    """
    if raw is None:
        return None
    if isinstance(raw, bytes):
        try:
            raw = raw.decode("utf-8")
        except UnicodeDecodeError:
            return repr(raw)

    s = raw.strip()
    if not ((s.startswith("{") and s.endswith("}")) or (s.startswith("[") and s.endswith("]"))):
        return s

    try:
        parsed = json.loads(s)
        return json.dumps(parsed, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    except (json.JSONDecodeError, TypeError, ValueError):
        return s
