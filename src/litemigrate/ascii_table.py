"""Lightweight ASCII table formatter."""
from __future__ import annotations

def format_ascii_table(headers: list[str], rows: list[list[str]]) -> str:
    cols = len(headers)
    widths = [len(h) for h in headers]
    for row in rows:
        for i in range(cols):
            if i < len(row):
                widths[i] = max(widths[i], len(str(row[i])))

    sep = "+-" + "-+-".join("-" * w for w in widths) + "-+"
    hdr = "| " + " | ".join(h.ljust(widths[i]) for i, h in enumerate(headers)) + " |"

    body_lines = []
    for row in rows:
        formatted = [str(row[i]).ljust(widths[i]) if i < len(row) else "".ljust(widths[i]) for i in range(cols)]
        body_lines.append("| " + " | ".join(formatted) + " |")

    return "\n".join([sep, hdr, sep] + body_lines + [sep])
