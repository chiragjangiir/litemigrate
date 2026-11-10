# LiteMigrate — Build Plan & Execution Roadmap

**Objective:** Transform LiteMigrate from a validated experimental prototype into a production-grade, installable Python package, clean CLI utility, and open-source GitHub repository.

---

## Milestone 1: Source Reconciliation & Foundation (Current)
- [x] Inspect existing workspace, reports, and prototype implementation.
- [x] Create untouched preservation archive in `phase3_backup/`.
- [x] Author `PROJECT_STATUS.md` and `IMPLEMENTATION_GAPS.md`.
- [x] Author `BUILD_PLAN.md`.

## Milestone 2: Product Core & Architecture Refactoring
- [ ] Establish standard `src/` layout:
  ```text
  litemigrate/
  ├── pyproject.toml
  ├── src/
  │   └── litemigrate/
  │       ├── __init__.py
  │       ├── models.py          # Enums, dataclasses, verdicts, reports
  │       ├── exceptions.py      # Structured exception hierarchy
  │       ├── sqlite_backend.py  # Hardened SQLite connections, PRAGMAs, C API
  │       ├── cloning.py         # APFS, FICLONE, and Bounded Backup cloning
  │       ├── fingerprint.py     # Canonical cell, row-identity, and column hashing
  │       ├── policy.py          # Migration policy definitions and validation
  │       ├── validation.py      # Schema/table/FK/integrity checks
  │       ├── promotion.py       # Atomic CAS promotion, lockfiles, rollbacks
  │       ├── engine.py          # Unified LiteMigrateEngine orchestrator
  │       └── cli.py             # Rich, robust CLI implementation
  ```
- [ ] Implement Gap A resolution: Reject arbitrary Python callables in public API; enforce SQL script migration atomicity.
- [ ] Implement Gap B resolution: Implement row-identity-aware streaming column fingerprinting supporting rowid and `WITHOUT ROWID` primary keys.
- [ ] Implement Gap E/F resolution: Robust `libsqlite3` C API binding with deadline timeouts and macOS `clonefile(2)` support.

## Milestone 3: Command-Line Interface (CLI)
- [ ] Implement `litemigrate --help`: Clear guidance, usage examples, safety notes.
- [ ] Implement `litemigrate inspect`: Inspect database size, journal mode, schema objects, tables, SQLite version, and basic integrity.
- [ ] Implement `litemigrate validate`: Run isolated shadow verification without touching source; output structured report.
- [ ] Implement `litemigrate apply`: Require explicit confirmation, create pre-promotion rollback backup, execute atomic CAS promotion, output backup path and audit summary.
- [ ] Implement `litemigrate report`: Display previously generated JSON audit reports.
- [ ] Support `--json` flag across all commands for CI/CD automation.

## Milestone 4: Comprehensive Test Suite & Quality Verification
- [ ] Migrate and verify:
  - Unit tests for fingerprinting, cell encoding, SQL statement splitting, policies.
  - Integration tests for shadow migration lifecycle, foreign key cascade catches, dropped objects.
  - Adversarial tests for TOCTOU concurrency (`C-01`, `C-02`), bounded timeouts (`C-03`), symlink safety (`S-02`), file permissions (`S-01`), and untrusted schema (`S-03`).
  - Native tests for macOS APFS `clonefile(2)` and `SQLITE_BACKUP_API`.
- [ ] Packaging validation: `pip install -e .` and verify imports from outside repo root.
- [ ] Configure GitHub Actions workflows (`tests.yml`, `lint.yml`) for Linux and macOS.

## Milestone 5: GitHub Repository & Release Candidate
- [ ] Initialize git repository in `litemigrate`.
- [ ] Add `.gitignore`, `pyproject.toml`, `LICENSE` (Apache-2.0 or MIT), `README.md`, `SECURITY.md`, `CONTRIBUTING.md`, `CHANGELOG.md`.
- [ ] Commit structured milestones with descriptive commit messages.
- [ ] Create public GitHub repository `chiragjangiir/litemigrate` via `gh repo create`.
- [ ] Push main branch and verify remote health.

## Milestone 6: Final Engineering Report
- [ ] Document final architecture, verified benchmark results, test coverage, limitations, and roadmap.
