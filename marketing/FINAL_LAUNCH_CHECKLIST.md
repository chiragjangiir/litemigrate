# LiteMigrate — Final Launch Checklist & Sequence

This document provides the definitive pre-flight checklist, launch sequence, and operational protocol for the public announcement of **LiteMigrate `v0.1.0-alpha.1`**.

---

## 1. Pre-Flight Verification Checklist

- [x] **Git Repository State**: Clean working tree on `main` branch, synchronized with `origin/main`.
- [x] **Release Tag**: `v0.1.0-alpha.1` points to immutable commit `e32b11d`.
- [x] **Distribution Assets**: Wheel, tarball, and `SHA256SUMS.txt` verified on GitHub Releases.
- [x] **Continuous Integration (CI)**: All 8 matrix configurations in `Tests` and `Lint & Typecheck` passing across Python 3.9–3.12 on macOS and Linux.
- [x] **First-Run Verification**: Clean virtual environment installation and walkthrough tested and verified.
- [x] **Documentation Accuracy**: All commands verified to match exact CLI arguments (`--db`, `--migration`, `--policy`).
- [x] **No Hyperbole / Overstatement**: Removed all claims of "zero risk", "100% safe", or "zero TOCTOU".
- [x] **Privacy Safeguards**: All feedback templates and outreach materials explicitly forbid uploading real or sensitive database files.

---

## 2. Launch Sequence

### Phase 1: Hacker News (Show HN)
- **Target**: Hacker News ([news.ycombinator.com](https://news.ycombinator.com)).
- **Title**: `Show HN: LiteMigrate – Validate SQLite migrations on a shadow database before promotion`
- **Copy**: Use Version 1 (Short & Direct) from [`marketing/SHOW_HN_POST.md`](SHOW_HN_POST.md).
- **First Comment**: If discussion expands on technical architecture, post excerpt from Version 2 explaining reflink cloning and CAS locks.
- **Timing**: Recommended weekday morning (between 13:00 and 15:00 UTC / 8:00 AM – 10:00 AM EST).
- **Monitoring Window**: Actively monitor thread for the first 4–6 hours to respond to technical questions using [`marketing/LAUNCH_RESPONSE_PLAYBOOK.md`](LAUNCH_RESPONSE_PLAYBOOK.md).

---

### Phase 2: Observation & Feedback Triage (24–48 Hours)
- **Actions**:
  - Do not post to other communities immediately.
  - Triage any bug reports, platform edge cases, or friction points raised by initial HN readers.
  - Tag incoming issues under `alpha` and `bug` / `compatibility`.

---

### Phase 3: Reddit (r/Python)
- **Target**: [reddit.com/r/Python](https://reddit.com/r/Python).
- **Title**: `[Project] LiteMigrate: Pre-validate SQLite migrations on an isolated shadow copy before promotion`
- **Copy**: Use [`marketing/REDDIT_R_PYTHON_POST.md`](REDDIT_R_PYTHON_POST.md).
- **Flair**: `Project`.
- **Timing**: 48 hours after Show HN, incorporating any initial technical feedback received from HN.

---

### Phase 4: Specialist Communities (Subsequent Weeks)
- **Target**: SQLite Forum / r/sqlite.
- **Copy**: Use SQLite-specific inquiry template from [`docs/ALPHA_TESTER_OUTREACH.md`](../docs/ALPHA_TESTER_OUTREACH.md).
- **Focus**: Seek targeted feedback on locking primitives (`BEGIN IMMEDIATE`), schema cookies, and row hashing.

---

## 3. Communication Rules & Boundaries

- **Zero Spam**: Never post identical messages across multiple subreddits or forums.
- **No Upvote Solicitations**: Never ask colleagues, friends, or social media followers to upvote or comment on HN or Reddit.
- **Stay Humble & Objective**: Emphasize that `v0.1.0-alpha.1` is an experimental pre-release seeking verification.
