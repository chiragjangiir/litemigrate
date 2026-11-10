# LiteMigrate — Growth Measurement & Community Metrics Framework

This document defines the metrics framework, measurement methodology, baseline values, and growth milestones for **LiteMigrate**.

In accordance with LiteMigrate's core principles, all metrics must be **verifiable, measured from actual repository data, and completely free of artificial manipulation or fabricated engagement.**

---

## 1. Metrics Definitions & Collection Methodology

| Metric | Source / Measurement Method | Command / Endpoint |
|:---|:---|:---|
| **GitHub Stars** | Total organic repository stars | `gh api repos/chiragjangiir/litemigrate --jq '.stargazer_count'` |
| **Unique Visitors** | 14-day rolling unique visitors | `gh api repos/chiragjangiir/litemigrate/traffic/views --jq '{count, uniques}'` |
| **Unique Git Clones** | 14-day rolling unique clones | `gh api repos/chiragjangiir/litemigrate/traffic/clones --jq '{count, uniques}'` |
| **Release Downloads** | Cumulative asset downloads for published releases | `gh api repos/chiragjangiir/litemigrate/releases --jq '.[].assets[] | {name, download_count}'` |
| **Independent Testers** | Distinct non-maintainer users opening issues or submitting reports | GitHub Issues filter: `label:alpha -author:chiragjangiir` |
| **External Contributors** | Distinct non-maintainer contributors with merged PRs | `git shortlog -sn --all` |
| **Issues & Discussions** | Genuine bug reports, compatibility logs, and UX threads | GitHub Issues & Discussions count |
| **Repeat Engagement** | Testers submitting multiple reports or participating in PR reviews | Contributor issue history |

---

## 2. Empirical Baseline (Measured as of 2026-11-10)

> [!NOTE]
> The baseline below represents the exact measured state at the conclusion of Phase 6A. Values are genuine and unmanipulated.

| Metric | Baseline Value (2026-11-10) | Notes |
|:---|:---:|:---|
| **GitHub Stars** | **0** | Clean launch baseline |
| **Forks** | **0** | Clean launch baseline |
| **14-Day Unique Visitors** | **0** | Repository newly opened |
| **14-Day Unique Clones** | **0** | Repository newly opened |
| **Release Downloads (`v0.1.0-alpha.1`)** | | |
| • `litemigrate-0.1.0a1-py3-none-any.whl` | **2** | Verification downloads by author |
| • `litemigrate-0.1.0a1.tar.gz` | **2** | Verification downloads by author |
| • `SHA256SUMS.txt` | **2** | Verification downloads by author |
| **External Issues Opened** | **0** | Baseline before external outreach |
| **External Pull Requests** | **0** | Baseline before external outreach |
| **Verified Test Suite Size** | **80 tests** | 100% CI pass rate across Python 3.9–3.12 |

---

## 3. Growth Milestones (Targets vs. Measurements)

Milestones are organized into three sequential horizons:

### Horizon 1: Alpha Reliability & Initial Tester Cohort (Month 1)
- **Primary Goal**: Gather genuine compatibility reports across Linux distros, macOS, and Windows.
- **Targets**:
  - 10+ independent testers opening Alpha feedback issues.
  - 25+ unique weekly clones.
  - 50+ total release wheel downloads.
  - Identification and remediation of any subtle filesystem locking edge cases.

### Horizon 2: Community Recognition & Developer Adoption (Months 2–3)
- **Primary Goal**: Establish LiteMigrate as the standard pre-promotion safety tool in the Python and SQLite ecosystems.
- **Targets**:
  - 100+ GitHub stars (organic developer interest).
  - 500+ release downloads.
  - 3+ external community code or documentation contributions.
  - Adoption in at least 2 open-source Python or local-first projects.

### Horizon 3: Beta Readiness & Ecosystem Integration (Months 4–6)
- **Primary Goal**: Transition from Alpha to stable Beta, culminating in PyPI publication.
- **Targets**:
  - 500+ GitHub stars.
  - 2,000+ downloads.
  - CI action published (GitHub Action for LiteMigrate).
  - Official PyPI release (`v0.2.0-beta.1`).

---

## 4. Weekly Metrics Audit Script

To ensure reproducible reporting, run this one-line script to audit live numbers:

```bash
python3 -c '
import subprocess, json

def gh(endpoint):
    res = subprocess.run(["gh", "api", endpoint], capture_output=True, text=True)
    return json.loads(res.stdout) if res.returncode == 0 else {}

repo = gh("repos/chiragjangiir/litemigrate")
print("=== LITEMIGRATE LIVE METRICS ===")
print("Stars:", repo.get("stargazers_count", 0))
print("Forks:", repo.get("forks_count", 0))
print("Open Issues:", repo.get("open_issues_count", 0))

rel = gh("repos/chiragjangiir/litemigrate/releases/tags/v0.1.0-alpha.1")
assets = rel.get("assets", [])
print("\n=== RELEASE ASSETS ===")
for a in assets:
    print(f"• {a[\"name\"]}: {a[\"download_count\"]} downloads")
'
```
