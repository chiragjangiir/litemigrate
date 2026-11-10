# Destructive Migration Example

Demonstrates LiteMigrate's strict default policy model and explicit allowlisting for destructive operations.

## Step 1: Create the baseline database

```bash
sqlite3 app.db < schema.sql
```

## Step 2: Attempt validation without policy (Blocked by default!)

```bash
litemigrate validate --db ./app.db --migration ./002_drop_legacy_audit.sql
```

Output:
```text
Verdict: BLOCKED_UNEXPECTED_TABLE_DROP
Audit Findings & Details:
  • Unexpected dropped table 'legacy_audit_log' was not declared in policy.allowed_dropped_tables.
```

LiteMigrate refuses to let any table be dropped silently.

## Step 3: Validate with explicit policy declaration

```bash
litemigrate validate --db ./app.db --migration ./002_drop_legacy_audit.sql --policy ./policy.json
```

Output:
```text
Verdict: PASSED
Audit Findings & Details:
  • Shadow validation passed: all schema, data, foreign key, and integrity invariants satisfied.
```

## Step 4: Apply with confirmation

```bash
litemigrate apply --db ./app.db --migration ./002_drop_legacy_audit.sql --policy ./policy.json --confirm
```
