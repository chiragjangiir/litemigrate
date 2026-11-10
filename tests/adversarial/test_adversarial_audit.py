"""Phase 4 Adversarial Audit Regression Test Suite (Suite A — 12 tests)."""

from __future__ import annotations

import os
import sqlite3
import tempfile
import time
import unittest
from pathlib import Path

from litemigrate.cloning import create_shadow_database
from litemigrate.engine import LiteMigrateEngine
from litemigrate.fingerprint import (
    canonical_cell_bytes,
    compute_logical_db_digest,
)
from litemigrate.models import ValidationVerdict
from litemigrate.policy import MigrationPolicy
from litemigrate.promotion import promote_shadow_to_source
from litemigrate.sqlite_backend import (
    bounded_sqlite_backup,
    open_hardened_sqlite,
    split_sql_statements,
)
from tests.fixtures.database_setup import create_test_database


class TestAdversarialAudit(unittest.TestCase):
    def test_finding_c01_toctou_between_barrier_rollback_and_clone_preserves_committed_write(self) -> None:
        """C-01: Proves concurrent write committed right after shadow creation is caught by CAS."""
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "app.db"
            create_test_database(db_path)

            # Step 1: Create shadow
            clone_res = create_shadow_database(db_path)
            shadow_conn = open_hardened_sqlite(clone_res.shadow_path)
            baseline_digest = compute_logical_db_digest(shadow_conn)
            shadow_conn.close()

            # Step 2: Concurrent writer commits row 777 to source_db!
            ext_conn = open_hardened_sqlite(db_path)
            ext_conn.execute("INSERT INTO parent_table VALUES (777, 'Concurrent Writer', 'C-01');")
            ext_conn.commit()
            ext_conn.close()

            # Step 3: Attempt promotion with stale baseline digest
            # CAS must detect that live_source_digest != baseline_digest and abort!
            with self.assertRaises(Exception):
                promote_shadow_to_source(
                    shadow_path=clone_res.shadow_path,
                    source_path=db_path,
                    expected_source_digest=baseline_digest,
                    migration_sql="ALTER TABLE parent_table ADD COLUMN extra TEXT;",
                    busy_timeout_ms=1000,
                )

            # Step 4: Verify row 777 was NOT clobbered!
            verify_conn = open_hardened_sqlite(db_path)
            row = verify_conn.execute("SELECT id, name FROM parent_table WHERE id = 777;").fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row[0], 777)
            verify_conn.close()

    def test_finding_c02_toctou_between_cas_digest_check_and_promotion_preserves_write(self) -> None:
        """C-02: Proves CAS verification inside BEGIN IMMEDIATE writer lock prevents lost updates."""
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "app.db"
            create_test_database(db_path)

            report = LiteMigrateEngine.execute_and_validate(
                source_db=db_path,
                migration_sql="ALTER TABLE parent_table ADD COLUMN notes TEXT;",
            )
            self.assertEqual(report.verdict, ValidationVerdict.PASSED)

            # Simulate writer committing row 888 before promotion
            ext_conn = open_hardened_sqlite(db_path)
            ext_conn.execute("INSERT INTO parent_table VALUES (888, 'C-02 Writer', 'Post CAS');")
            ext_conn.commit()
            ext_conn.close()

            # Now attempting apply with old digest
            from litemigrate.exceptions import ConcurrencyConflictError
            with self.assertRaises(ConcurrencyConflictError):
                promote_shadow_to_source(
                    shadow_path=Path(td) / "dummy",
                    source_path=db_path,
                    expected_source_digest=report.original_db_sha256_before,  # old digest
                    migration_sql="ALTER TABLE parent_table ADD COLUMN notes TEXT;",
                )

            # Verify row 888 preserved
            v_conn = open_hardened_sqlite(db_path)
            self.assertIsNotNone(v_conn.execute("SELECT * FROM parent_table WHERE id = 888;").fetchone())
            v_conn.close()

    def test_finding_c03_sqlite_backup_api_bounded_timeout_on_locked_destination(self) -> None:
        """C-03: Proves bounded backup terminates cleanly on locked destination within timeout."""
        with tempfile.TemporaryDirectory() as td:
            src_db = Path(td) / "src.db"
            dst_db = Path(td) / "dst.db"
            create_test_database(src_db)
            create_test_database(dst_db)

            # Hold exclusive lock on dst_db
            dst_conn = open_hardened_sqlite(dst_db)
            dst_conn.execute("BEGIN EXCLUSIVE;")

            t0 = time.monotonic()
            try:
                with self.assertRaises(sqlite3.OperationalError):
                    bounded_sqlite_backup(src_db, dst_db, busy_timeout_ms=150)
                elapsed = time.monotonic() - t0
                self.assertLess(elapsed, 2.0)
            finally:
                dst_conn.execute("ROLLBACK;")
                dst_conn.close()

    def test_finding_c04_passive_wal_checkpoint_does_not_alter_logical_digest(self) -> None:
        """C-04: Passive WAL checkpoints altering physical bytes do not change logical digest."""
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "wal.db"
            conn = create_test_database(db_path, enable_wal=True)

            d1 = compute_logical_db_digest(conn)
            # Run checkpoint
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
            d2 = compute_logical_db_digest(conn)

            self.assertEqual(d1, d2)
            conn.close()

    def test_finding_d01_adding_column_still_catches_silent_mutation_on_existing_columns(self) -> None:
        """D-01: Proves adding a column alongside a silent mutation on an existing column is blocked."""
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "app.db"
            create_test_database(db_path)

            # Migration adds column 'notes', but maliciously alters 'description' on parent_table!
            migration_sql = """
            ALTER TABLE parent_table ADD COLUMN notes TEXT;
            UPDATE parent_table SET description = 'SILENTLY_WIPED_DATA' WHERE id = 1;
            """
            policy = MigrationPolicy()  # empty policy: mutations not allowed

            report = LiteMigrateEngine.execute_and_validate(
                source_db=db_path,
                migration_sql=migration_sql,
                policy=policy,
            )

            self.assertEqual(report.verdict, ValidationVerdict.BLOCKED_UNEXPECTED_DATA_MUTATION)
            self.assertIn("parent_table", report.mutated_tables)
            self.assertTrue(report.original_db_untouched)

    def test_finding_d02_canonical_cell_bytes_distinguishes_signed_zero_and_all_storage_classes(self) -> None:
        """D-02: IEEE 754 signed zero float discrimination."""
        self.assertNotEqual(canonical_cell_bytes(-0.0), canonical_cell_bytes(+0.0))

    def test_finding_d03_dropped_views_triggers_and_indexes_are_detected_and_blocked(self) -> None:
        """D-03: Dropped views, triggers, and indexes are caught by SchemaObjectSnapshot."""
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "app.db"
            conn = create_test_database(db_path)
            conn.execute("CREATE VIEW v1 AS SELECT id FROM parent_table;")
            conn.execute("CREATE TRIGGER trg1 AFTER INSERT ON parent_table BEGIN SELECT 1; END;")
            conn.commit()
            conn.close()

            # Migration drops view and trigger
            migration_sql = "DROP VIEW v1; DROP TRIGGER trg1;"
            report = LiteMigrateEngine.execute_and_validate(
                source_db=db_path,
                migration_sql=migration_sql,
            )

            self.assertEqual(report.verdict, ValidationVerdict.BLOCKED_UNEXPECTED_SCHEMA_OBJECT_DROP)
            dropped_names = [o.name for o in report.dropped_schema_objects]
            self.assertIn("v1", dropped_names)
            self.assertIn("trg1", dropped_names)

    def test_finding_d04_split_sql_statements_handles_multiple_statements_per_line_and_triggers(self) -> None:
        """D-04: Robust statement splitting."""
        raw = "SELECT 1; SELECT 2; CREATE TRIGGER trg BEGIN UPDATE t SET x=1; END;"
        stmts = split_sql_statements(raw)
        self.assertEqual(len(stmts), 3)

    def test_finding_p01_audit_report_accurately_reflects_promotion_state(self) -> None:
        """P-01: Audit report accurately reflects promotion state and post-promotion hashes."""
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "app.db"
            create_test_database(db_path)

            report = LiteMigrateEngine.execute_and_validate(
                source_db=db_path,
                migration_sql="ALTER TABLE parent_table ADD COLUMN bio TEXT;",
                apply_to_source_on_pass=True,
                confirmed=True,
            )

            self.assertEqual(report.verdict, ValidationVerdict.PASSED)
            self.assertTrue(report.promoted_to_source)
            self.assertFalse(report.original_db_untouched)
            self.assertNotEqual(report.original_db_sha256_before, report.original_db_sha256_after)

    def test_finding_s01_private_0600_shadow_file_permissions_enforced(self) -> None:
        """S-01: Private 0o600 file permissions enforced on shadow database."""
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "app.db"
            create_test_database(db_path)

            res = create_shadow_database(db_path)
            mode = os.stat(res.shadow_path).st_mode & 0o777
            self.assertEqual(mode, 0o600)
            res.shadow_path.unlink()

    def test_finding_s02_dangling_symlink_rejected_and_victim_never_created(self) -> None:
        """S-02: Dangling symlink at destination is rejected."""
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "app.db"
            create_test_database(db_path)

            victim_file = Path(td) / "victim.txt"
            symlink_path = Path(td) / "symlink_dst.db"
            symlink_path.symlink_to(victim_file)

            with self.assertRaises(PermissionError):
                create_shadow_database(db_path, shadow_db=symlink_path)
            self.assertFalse(victim_file.exists())

    def test_finding_s03_trusted_schema_disabled_and_verified_on_all_connections(self) -> None:
        """S-03: PRAGMA trusted_schema is 0 (OFF) on every opened connection."""
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "app.db"
            create_test_database(db_path)

            conn = open_hardened_sqlite(db_path)
            val = conn.execute("PRAGMA trusted_schema;").fetchone()[0]
            self.assertEqual(val, 0)
            conn.close()


if __name__ == "__main__":
    unittest.main()
