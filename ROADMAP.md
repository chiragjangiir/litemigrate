# LiteMigrate — Technical Feature Roadmap

This document outlines the prioritized, value-driven technical roadmap for **LiteMigrate**.

In alignment with our engineering principles, we do not add speculative features or inflate the roadmap for vanity. Every proposal addresses a concrete developer problem, evaluates technical complexity and safety implications, and requires empirical evidence before implementation begins.

---

## Roadmap Overview

```
Horizon 1 (Alpha Focus):       Reliability, Usability & Explanations
                               ├── Proposal 4: Better Validation Explanations
                               └── Proposal 2: Human-Readable Schema Diffs

Horizon 2 (Beta Preparation):  Developer Ergonomics & CI Automation
                               ├── Proposal 3: Migration Impact Summaries
                               ├── Proposal 5: Audit Report Enhancements
                               └── Proposal 6: GitHub Actions / CI Integration

Horizon 3 (Advanced Safety):   Deep AST Analysis
                               └── Proposal 1: Schema & DDL AST Analysis
```

---

## Detailed Proposal Evaluations

### Proposal 1: Schema & DDL AST Analysis

- **User Problem**: Currently, LiteMigrate evaluates migrations by executing SQL statements sequentially on the shadow database. While effective, it cannot proactively warn developers about risky SQL patterns (e.g. `DROP COLUMN` on SQLite < 3.35, unindexed foreign key lookups, or multi-step rebuilds lacking index recreations) prior to shadow execution.
- **Expected Value**: Static pre-flight warnings before executing SQL on the shadow clone; detection of syntax unsupported on specific SQLite versions.
- **Technical Complexity**: **High**. Writing a full SQL parser for SQLite dialect is prone to edge cases, and external parser dependencies (e.g., `sqlglot` or `sqlparse`) add significant weight.
- **Safety Implications**: **Neutral to Positive**. Must only act as an advisory pre-flight linter; it must *never* replace runtime shadow validation.
- **Dependencies**: Potential lightweight tokenizer or AST parser.
- **Evidence Needed Before Implementation**: User feedback showing developers frequently write syntax that fails mid-migration on older SQLite runtimes, or demand for automated linting in CI.
- **Priority**: **Horizon 3 (Post-Beta)**.

---

### Proposal 2: Human-Readable Schema Diffs

- **User Problem**: When schema changes occur, `AuditReport` currently outputs raw table schema object snapshots or list differences. Developers want to see clean, Git-style visual schema diffs in the terminal (e.g., `+ column_name TEXT DEFAULT ''`, `- old_index`).
- **Expected Value**: Instant visual comprehension of schema modifications during `litemigrate validate` without needing to parse JSON.
- **Technical Complexity**: **Low to Medium**. Involves formatting differences between `tables_before` and `tables_after` dataclasses using standard library `difflib`.
- **Safety Implications**: **Zero**. Formatting enhancement only; zero impact on validation invariants.
- **Dependencies**: None (uses standard library `difflib`).
- **Evidence Needed Before Implementation**: Community feedback on CLI usability requesting colored or visual schema diffing.
- **Priority**: **Horizon 1 (Immediate Alpha Improvement)**.

---

### Proposal 3: Migration Impact Summaries

- **User Problem**: Large migrations affecting multiple tables make it difficult for operators to understand the full blast radius. Developers need a high-level summary: "3 tables modified, 1 index added, 14,250 rows verified, 0 rows deleted."
- **Expected Value**: Executive clarity for database operators and reviewers before executing `litemigrate apply --confirm`.
- **Technical Complexity**: **Low**. Aggregate existing `TableSnapshot` counts into an `ImpactSummary` dataclass.
- **Safety Implications**: **Positive**. Enhances operator awareness and reduces accidental approvals.
- **Dependencies**: None.
- **Evidence Needed Before Implementation**: Requests from database administrators and platform engineers managing multi-table schemas.
- **Priority**: **Horizon 2 (Early Beta)**.

---

### Proposal 4: Better Validation Explanations & Actionable Remediation

- **User Problem**: When validation fails (e.g., `BLOCKED_FOREIGN_KEY_VIOLATION` or `BLOCKED_UNEXPECTED_TABLE_DROP`), the error message tells the user *what* broke, but does not provide actionable remediation steps (e.g., "Declare table in policy.json or ensure parent records are inserted first").
- **Expected Value**: Drastically reduces developer friction when troubleshooting failed migrations.
- **Technical Complexity**: **Low**. Map each `ValidationVerdict` to a structured explanation and remediation hint.
- **Safety Implications**: **Positive**. Educates users on safe SQLite practices without weakening safety checks.
- **Dependencies**: None.
- **Evidence Needed Before Implementation**: Feedback from Alpha tester issue reports encountering confusion over policy rejections.
- **Priority**: **Horizon 1 (Immediate Alpha Improvement)**.

---

### Proposal 5: Audit Report Enhancements (HTML / Markdown Export)

- **User Problem**: Teams running migrations in collaborative workflows want to attach audit reports to pull requests or compliance records in Markdown or HTML format, rather than sharing raw JSON.
- **Expected Value**: Enables teams to use LiteMigrate as a compliance and audit record in SOC2 or enterprise change management workflows.
- **Technical Complexity**: **Medium**. Create templated Markdown and standalone HTML export formatters.
- **Safety Implications**: **Zero**. Pure reporting enhancement.
- **Dependencies**: Optional Jinja2 or lightweight Python string templates.
- **Evidence Needed Before Implementation**: Enterprise or platform team feedback requesting compliance-friendly reporting.
- **Priority**: **Horizon 2 (Beta)**.

---

### Proposal 6: GitHub Actions & CI/CD Integration

- **User Problem**: Teams want to automatically validate SQLite migrations in pull requests against realistic sanitized database snapshots before merging code.
- **Expected Value**: Catches destructive migrations, foreign key violations, and performance issues in CI before code ever reaches production.
- **Technical Complexity**: **Medium**. Build a pre-packaged composite GitHub Action (`chiragjangiir/litemigrate-action`) that runs `litemigrate validate` and comments the audit report directly on pull requests.
- **Safety Implications**: **Positive**. Extends shift-left safety to the entire development team.
- **Dependencies**: GitHub Actions runner environment.
- **Evidence Needed Before Implementation**: Stable Beta CLI release (`v0.2.0-beta.1`) and PyPI package publication.
- **Priority**: **Horizon 2 (Beta Milestone)**.

---

## Roadmap Summary Matrix

| Proposal | Target Horizon | User Value | Complexity | Safety Impact | Recommended Status |
|:---|:---:|:---:|:---:|:---:|:---:|
| **Better Explanations & Remediation** | Horizon 1 | High | Low | Positive | **Candidate for v0.1.1** |
| **Human-Readable Schema Diffs** | Horizon 1 | High | Low–Med | Neutral | **Candidate for v0.1.1** |
| **Migration Impact Summaries** | Horizon 2 | Med–High | Low | Positive | **Planned for v0.2.0-beta.1** |
| **Audit Report Markdown/HTML** | Horizon 2 | Medium | Medium | Neutral | **Planned for v0.2.0-beta.1** |
| **GitHub Actions CI Integration** | Horizon 2 | Very High | Medium | Positive | **Planned for v0.2.0-beta.1** |
| **Schema & DDL AST Analysis** | Horizon 3 | Medium | High | Neutral | **Under Research** |

