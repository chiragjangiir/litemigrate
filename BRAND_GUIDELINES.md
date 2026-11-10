# LiteMigrate — Brand & Identity Guidelines

This document defines the visual, aesthetic, and written identity for **LiteMigrate**.

LiteMigrate is an infrastructure safety tool. Its brand identity must communicate engineering rigor, mathematical precision, and technical restraint. It must feel like an established, trustworthy Unix utility—not an AI-generated SaaS startup or marketing gimmick.

---

## 1. Core Visual Identity

### Aesthetic Philosophy
- **Restrained & Functional**: No gradient swooshes, cartoon illustrations, or hyperactive landing page animations.
- **Terminal-Native**: Looks native inside dark or light terminal emulators, developer IDEs, and GitHub markdown.
- **Precision-First**: Clean lines, monospace data tables, explicit box-drawing characters, and unambiguous status badges.

---

## 2. Logo Concepts & Recommended Direction

### Recommended Concept: "The Shadow Vault"
A structural SQLite database cylinder casting an offset, transactionally isolated "shadow" copy underneath, with an audit verification checkpoint separating them.

#### ASCII Terminal Mark:
```text
      ┌─────────────┐
     /             /│
    ┌─────────────┐ │
    │   SOURCE    │ │
    │  DATABASE   │ │
    └─────────────┘ ┼ ─ ─ ─ ─ ─ ─ ─ ─ (Source DB Untouched)
           │
           ▼
     . - - - - - - .
    :    SHADOW   : │  [ INVARIANT VERIFICATION ]
    :   SANDBOX   : │  • Integrity Check
    :             : │  • Foreign Key Audit
     `- - - - - - ' ┘  • Row Fingerprinting
```

#### SVG Vector Specification:
- **Geometry**: Two stacked 2.5D isometric cylinders. The top cylinder is drawn with crisp solid strokes (representing the active source database). The bottom cylinder is drawn with dashed or tinted geometry (representing the isolated shadow layer). A verification prism sits between them.
- **Aspect Ratio**: 1:1 icon mark, 4:1 horizontal wordmark for GitHub banners.

---

## 3. Color Palette

LiteMigrate adopts a subdued, terminal-inspired palette:

| Role | Color Name | Hex Code | Usage |
|:---|:---|:---|:---|
| **Primary Base** | Deep Slate | `#0F172A` | Backgrounds, dark mode terminal headers |
| **Surface** | Dark Charcoal | `#1E293B` | Code blocks, borders, table headers |
| **Foreground Text** | Clean Silver | `#E2E8F0` | Primary documentation and terminal text |
| **Muted Text** | Subdued Gray | `#94A3B8` | Secondary metadata, timestamps, hashes |
| **Safety Accent (Pass)** | Verified Emerald | `#10B981` | Passing checks, successful promotions, `PASSED` |
| **Safety Accent (Block)**| Warning Amber | `#F59E0B` | Policy rejections, schema diff alerts |
| **Failure Accent** | Hard Stop Coral | `#EF4444` | Integrity failures, foreign key violations |
| **Shadow Accent** | Cyan Indigo | `#6366F1` | Shadow clone indicators, copy-on-write metrics |

---

## 4. Typography

- **Documentation Prose**: Modern, high-legibility sans-serif: Inter, system-ui, or SF Pro.
- **Code & CLI Commands**: Clean monospace font: JetBrains Mono, Fira Code, or SF Mono.
- **Hierarchy**:
  - `# Title`: 24pt bold, crisp sentence case.
  - `## Section`: 18pt bold with horizontal divider (`---`).
  - `### Subsection`: 14pt bold.
  - Body: 11-12pt regular with 1.5 line height.

---

## 5. Written Identity & Tone of Voice

### Core Attributes
- **Sober & Accurate**: State facts and measurement data. Never exaggerate or make unfalsifiable claims.
- **Empirically Grounded**: Cite exact SQLite PRAGMAs, system calls (`clonefile`, `FICLONE`), and test metrics.
- **Transparent About Limits**: Prominently state what LiteMigrate does *not* do. Do not hide caveats.
- **Respectful of Developer Autonomy**: Developers own their schemas. LiteMigrate provides safety boundaries, not arbitrary dogma.

### Tone Comparisons (What to Say vs. What NOT to Say)

| Avoid (Hype / Misleading) | Prefer (Precise / Engineering-Grounded) |
|:---|:---|
| ❌ "Zero-TOCTOU guarantee across all systems forever!" | ✅ "Atomic CAS check using `PRAGMA data_version` and schema cookies under an exclusive `BEGIN IMMEDIATE` writer lock." |
| ❌ "The ultimate AI migration platform for modern web apps." | ✅ "A local-first SQLite migration safety utility that tests schema and data invariants against an isolated shadow copy before promotion." |
| ❌ "Guarantees 100% bug-free migrations every single time." | ✅ "Detects foreign key violations, page corruption, undeclared table drops, and row loss before modifying source files." |
| ❌ "Works seamlessly with every database engine." | ✅ "Engineered specifically for SQLite." |
| ❌ "Zero performance overhead." | ✅ "Sub-millisecond clone time (< 1 ms on APFS/reflink) with streaming row fingerprinting." |

---

## 6. Terminal Output Guidelines

All CLI commands adhere to strict output conventions:
- **Consistent Frame**: Enclosed within 65-character double-line borders (`═════════════════════════════════════════════════════════════════`).
- **Verdicts First**: Verdict is immediately visible on line 4 (`Verdict: PASSED`, `Verdict: BLOCKED_FOREIGN_KEY_VIOLATION`).
- **Deterministic Exit Codes**:
  - `0`: Validation passed / Migration successfully promoted.
  - `1`: Validation blocked by safety invariant violation or execution error.
  - `2`: CLI argument or syntax error.
- **No Mystery Writes**: When validation fails or runs in inspection mode, the banner explicitly asserts: `Source DB Untouched: Yes`.
