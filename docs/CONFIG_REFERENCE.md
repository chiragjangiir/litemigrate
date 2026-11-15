# LiteMigrate Configuration Reference

This guide details all configuration options supported by LiteMigrate via environment variables, CLI flags, or policy files.

---

## 1. Environment Variables

| Variable | Type | Default | Description |
|:---------|:-----|:--------|:------------|
| `LITEMIGRATE_TIMEOUT` | float | `10.0` | Maximum seconds to wait when acquiring an exclusive SQLite lock. |
| `LITEMIGRATE_STRATEGY`| string | `auto` | Preferred shadow cloning strategy (`auto`, `apfs_clonefile`, `copy`). |
| `LITEMIGRATE_BACKUP_DIR` | path | `None` | Custom directory to persist pre-promotion database backups. |
| `LITEMIGRATE_ENFORCE_FK` | bool | `true` | Enforce `PRAGMA foreign_keys = ON;` during shadow verification. |
| `LITEMIGRATE_WAL` | bool | `true` | Prefer Write-Ahead Logging (`PRAGMA journal_mode=WAL;`). |
| `LITEMIGRATE_MAX_MEMORY_MB` | int | `64` | Maximum allowable resident memory for fingerprinting cursors. |

---

## 2. Policy File (`policy.json`) Schema

```json
{
  "allow_destructive_changes": false,
  "allowed_dropped_tables": ["legacy_cache"],
  "allowed_dropped_columns": {
    "users": ["temp_session_token"]
  },
  "max_allowed_row_loss": 0
}
```
