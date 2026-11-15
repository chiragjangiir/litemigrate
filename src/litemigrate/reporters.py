"""
Report rendering utilities for human-readable and CI/CD step summary outputs.
"""

from __future__ import annotations

from typing import Any


def render_markdown_summary(
    verdict: str,
    duration_ms: float,
    fk_violations: int,
    integrity_ok: bool,
    tables_scanned: int,
) -> str:
    """Render a GitHub Flavored Markdown summary suitable for GITHUB_STEP_SUMMARY."""
    status_icon = "✅" if verdict.lower() == "passed" else "❌"
    integrity_icon = "PASSED" if integrity_ok else "FAILED"

    lines = [
        f"### {status_icon} LiteMigrate Shadow Validation Summary",
        "",
        "| Metric | Value |",
        "|:-------|:------|",
        f"| **Verdict** | `{verdict.upper()}` |",
        f"| **Total Elapsed** | {duration_ms:.2f} ms |",
        f"| **Foreign Key Violations** | {fk_violations} |",
        f"| **Database Integrity** | `{integrity_icon}` |",
        f"| **Tables Scanned** | {tables_scanned} |",
        "",
    ]
    return "\n".join(lines)
