# Contributing to LiteMigrate

Thank you for your interest in contributing to LiteMigrate!

LiteMigrate is an infrastructure safety tool where correctness and data preservation take priority over feature velocity. We welcome bug reports, test improvements, and well-reasoned enhancements.

---

## Engineering Principles

1. **No Silent Data Loss:** If a migration alters data or schemas in an undeclared way, the default must always be to block.
2. **Local-First & Offline:** LiteMigrate must function completely offline without external cloud dependencies or telemetry.
3. **No Unverified Claims:** Platform features (e.g. APFS cloning, Linux FICLONE) must be empirically verified on actual hardware before documentation claims are made.
4. **Preserve Documentation Integrity:** Ensure architecture documents, security reviews, and test assertions stay synchronized with the actual codebase.

---

## Local Development Workflow

### Prerequisites
- Python 3.9+
- SQLite 3.35+
- Standard C compiler and development headers (for `libsqlite3`)

### Setup

```bash
git clone https://github.com/chiragjangiir/litemigrate.git
cd litemigrate

python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### Running Tests

```bash
python -m unittest discover -v -s tests -t . -p "test_*.py"
```

### Running Benchmarks

```bash
python benchmark.py
```

### Code Style & Typechecking

```bash
ruff check src tests
mypy src
```

---

## Pull Request Guidelines

1. **Include Tests:** Every bug fix must include an adversarial regression test reproducing the defect before the fix.
2. **Atomic Commits:** Structure commits logically with descriptive messages explaining the engineering reason for each change.
3. **Safety Analysis:** If altering validation logic or concurrency locking, explain the safety implications in your PR description.
