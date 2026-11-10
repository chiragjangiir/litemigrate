# LiteMigrate — Phase 5 Regression Test Results

**Date:** November 10, 2026  
**Command Executed:** `python3 -m unittest discover -v -s . -p "test_*.py"`  
**Working Directory:** `/working_dir/c_bafdcdef1489d3a3/litemigrate_validation`  
**Total Tests Executed:** **38 tests across 4 suites**  
**Execution Time:** **`1.728s`**  
**Result:** **`OK` (38 / 38 Passed, 0 Failures, 0 Errors)**

---

## 1. Test Suite Breakdown

### Suite A: Phase 4 Adversarial Audit Regression Suite (`test_adversarial_audit.py` — 12/12 Passed)
Every adversarial proof-of-concept test that previously exposed a defect in Phase 4 now asserts and verifies the remediated behavior:

| Test Case | Finding Verified | Asserted Outcome | Result |
| :--- | :--- | :--- | :--- |
| `test_finding_c01_toctou_between_barrier_rollback_and_clone_preserves_committed_write` | `C-01` | Concurrent row `id=777` committed right after shadow creation is detected (`BLOCKED_SOURCE_MODIFIED_CONCURRENTLY`) and preserved on `source_db` | `PASS` |
| `test_finding_c02_toctou_between_cas_digest_check_and_promotion_preserves_write` | `C-02` | Concurrent row `id=888` committed before promotion lock acquisition is caught inside `_promote_shadow_to_source()` (`BLOCKED_SOURCE_MODIFIED_CONCURRENTLY`) and preserved | `PASS` |
| `test_finding_c03_sqlite_backup_api_bounded_timeout_on_locked_destination` | `C-03` | Subprocess calling `create_shadow_database` against an exclusively locked DB terminates cleanly within `< 1.5s` with `OperationalError: database is locked` | `PASS` |
| `test_finding_c04_passive_wal_checkpoint_does_not_alter_logical_digest` | `C-04` | `compute_logical_db_digest()` remains identical before and after `PRAGMA wal_checkpoint(TRUNCATE)` despite raw file SHA-256 changing | `PASS` |
| `test_finding_d01_adding_column_still_catches_silent_mutation_on_existing_columns` | `D-01` | `ALTER TABLE child_table ADD COLUMN notes` combined with `UPDATE child_table SET amount_cents = 0 WHERE id = 1` is blocked with `BLOCKED_UNEXPECTED_DATA_MUTATION` | `PASS` |
| `test_finding_d02_canonical_cell_bytes_distinguishes_signed_zero_and_all_storage_classes` | `D-02` | `_canonical_cell_bytes(-0.0) != _canonical_cell_bytes(+0.0)` and all 5 SQLite storage classes produce distinct canonical encodings | `PASS` |
| `test_finding_d03_dropped_views_triggers_and_indexes_are_detected_and_blocked` | `D-03` | `DROP VIEW`, `DROP TRIGGER`, and `DROP INDEX` are caught and blocked with `BLOCKED_UNEXPECTED_SCHEMA_OBJECT_DROP` | `PASS` |
| `test_finding_d04_split_sql_statements_handles_multiple_statements_per_line_and_triggers` | `D-04` | Multi-statement lines and `CREATE TRIGGER ... BEGIN ... END;` blocks parse into exact complete SQL statements via `sqlite3.complete_statement()` | `PASS` |
| `test_finding_p01_audit_report_accurately_reflects_promotion_state` | `P-01` | When `apply_to_source_on_pass=True` succeeds, `report.promoted_to_source is True`, `report.original_db_untouched is False`, and `original_db_sha256_after != original_db_sha256_before` | `PASS` |
| `test_finding_s01_private_0600_shadow_file_permissions_enforced` | `S-01` | Under `os.umask(0o022)`, shadow files created via `LINUX_FICLONE` and `SQLITE_BACKUP_API` have exact mode `0o600` (`-rw-------`) | `PASS` |
| `test_finding_s02_dangling_symlink_rejected_and_victim_never_created` | `S-02` | Dangling symlink at `shadow_path` raises `PermissionError` and never creates the symlink target | `PASS` |
| `test_finding_s03_trusted_schema_disabled_and_verified_on_all_connections` | `S-03` | `PRAGMA trusted_schema` reads back as `0` (`OFF`) on every connection | `PASS` |

---

### Suite B: Mandatory Phase 5 Remediation Test Suite (`test_phase5_remediation.py` — 12/12 Passed)

| Test Case | Phase 5 Mandatory Scenario | Result |
| :--- | :--- | :--- |
| `test_01_write_committed_after_shadow_creation_before_digest` | 1. Write committed after shadow creation but before digest verification | `PASS` |
| `test_02_write_attempted_after_digest_verification_before_promotion` | 2. Write committed/attempted after digest verification before promotion | `PASS` |
| `test_03_writer_holding_lock_during_backup_in_subprocess` | 3. Writer holding a lock during backup in an isolated subprocess with hard timeout (`< 1.5s`) | `PASS` |
| `test_04_interrupted_backup_leaves_source_database_intact` | 4. Interrupted promotion / mid-promotion failure leaves source database usable and intact | `PASS` |
| `test_05_added_column_alongside_destructive_update_to_existing_column` | 5. Added column alongside a destructive update to an existing column is blocked | `PASS` |
| `test_06_dropped_index_trigger_and_view_detection_and_policy_override` | 6. Dropped index, trigger, and view blocked by default and allowed when explicitly declared in policy | `PASS` |
| `test_07_0600_source_database_produces_0600_shadow_across_all_strategies` | 7. A `0600` source database produces a `0600` shadow across both `FICLONE` and `SQLITE_BACKUP_API` | `PASS` |
| `test_08_dangling_symlink_at_temporary_destination_rejected` | 8. Dangling symlink at temporary destination is rejected without touching target | `PASS` |
| `test_09_trusted_schema_read_back_on_every_connection` | 9. `PRAGMA trusted_schema` is read back and verified `0` (`OFF`) on every connection | `PASS` |
| `test_10_wal_checkpoint_activity_during_validation_does_not_abort` | 10. Passive/truncating WAL checkpoint activity during validation does not cause false CAS abort | `PASS` |
| `test_11_process_interruption_during_migration_and_promotion_cleans_up_workspace` | 11. Process interruption / exception during migration cleans up temporary `0o700` shadow directories | `PASS` |
| `test_12_two_litemigrate_processes_operating_on_same_source_database` | 12. Two LiteMigrate processes operating concurrently on the same source database serialize or safely block | `PASS` |

---

### Suite C: Original Phase 3 Shadow Migration Suite (`test_shadow_migration.py` — 10/10 Passed, `T-01` Remediated)

| Test Case | Scenario | Result |
| :--- | :--- | :--- |
| `test_01_normal_schema_migration` | Normal `ALTER TABLE ADD COLUMN` + `CREATE INDEX` promoted to source | `PASS` |
| `test_02_foreign_key_cascade_deletion_blocked` | Unintended `ON DELETE CASCADE` child row loss blocked | `PASS` |
| `test_03_explicitly_permitted_destructive_migration` | Policy-allowlisted row deletion permitted and promoted | `PASS` |
| `test_04_failed_migration_rollback_and_exception_handling` | Mid-migration `UNIQUE` constraint violation rolled back cleanly | `PASS` |
| `test_05_corrupted_shadow_database_detected` | B-tree interior page corruption caught by `PRAGMA integrity_check` | `PASS` |
| `test_06_active_wal_database_uncheckpointed_frames` | Active uncheckpointed `-wal` frames captured via `SQLITE_BACKUP_API` fallback | `PASS` |
| `test_07_concurrent_writer_lock_handling` | **Remediated `T-01`:** Short concurrent writer commits and full promotion (`apply_to_source_on_pass=True`) preserves both row `500` and column `conc_ok`; hung lock times out within `100ms` budget | `PASS` |
| `test_08_original_database_integrity_after_failed_validation` | Logical and byte integrity of `source_db` preserved after multiple failed migrations | `PASS` |
| `test_09_identical_row_counts_with_different_underlying_data` | Equal row counts (`120 == 120`) with mutated cell value caught by SHA-256 content hash | `PASS` |
| `test_10_backup_api_fallback_and_clone_strategy_verification` | **Remediated `T-01`:** Asserts exact `CloneStrategy.LINUX_FICLONE` on Linux XFS alongside `SQLITE_BACKUP_API` | `PASS` |

---

### Suite D: Foreign-Key Cascade & Table-Rebuild Suite (`test_foreign_key_cascade.py` — 4/4 Passed)

| Test Case | Scenario | Result |
| :--- | :--- | :--- |
| `test_atlas_3317_bug_reproduction_caught_by_shadow_auditor` | Reproduces [ariga/atlas #3317](https://github.com/ariga/atlas/issues/3317) (`DROP TABLE parent_table` with `foreign_keys=ON` wiping `100` child rows) and blocks promotion | `PASS` |
| `test_dangling_foreign_key_detected_after_rebuild` | Catches orphan foreign keys after table rebuild via `PRAGMA foreign_key_check` (`BLOCKED_FOREIGN_KEY_VIOLATION`) | `PASS` |
| `test_pragma_foreign_keys_is_noop_inside_transaction` | Proves SQLite's documented guarantee that `PRAGMA foreign_keys` is a no-op inside an active transaction | `PASS` |
| `test_safe_12_step_parent_rebuild_preserves_child_rows` | Verifies SQLite's 12-step table rebuild with `foreign_keys=OFF` outside the transaction preserves all `100` child rows | `PASS` |
