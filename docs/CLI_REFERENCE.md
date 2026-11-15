# LiteMigrate CLI Command Reference

This document provides a comprehensive command-line reference for the `litemigrate` CLI utility.

---

## Commands

### `inspect`
Inspect database schema, journal mode, foreign key status, and integrity.

```bash
litemigrate inspect --db <path-to-db> [--json]
```

---

### `validate`
Create an isolated shadow copy, execute migration, and audit safety invariants.

```bash
litemigrate validate --db <path-to-db> --migration <path-to-sql> [OPTIONS]
```

Options:
- `--policy <file>`: Path to JSON policy declaring permitted drops or schema mutations.
- `--strategy <strategy>`: Shadow cloning strategy (`auto`, `apfs_clonefile`, `copy`).
- `--output <file>`: Path to persist structured JSON audit report.
- `--summary`: Output a condensed summary table.
- `--json`: Output full audit report in JSON format.

---

### `apply`
Validate migration on shadow copy, require confirmation, and promote safely to source.

```bash
litemigrate apply --db <path-to-db> --migration <path-to-sql> --confirm [OPTIONS]
```

---

## Exit Codes

| Exit Code | Meaning |
|:----------|:--------|
| `0` | Success / Migration passed validation |
| `1` | Validation failed (invariant violation, unexpected drop, data loss) |
| `2` | Concurrency conflict or lock timeout |
| `3` | Security violation or permissions error |
| `5` | File not found or general operational error |
