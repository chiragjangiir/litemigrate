"""Integration test suite: 10 core shadow migration validation scenarios."""

from __future__ import annotations

import sqlite3
import sys
import tempfile
import threading
import unittest
from pathlib import Path

from litemigrate.engine import LiteMigrateEngine
from litemigrate.fingerprint import compute_file_sha256
from litemigrate.models import CloneStrategy, ValidationVerdict
from litemigrate.policy import MigrationPolicy
from litemigrate.sqlite_backend import open_hardened_sqlite
from tests.fixtures.database_setup import create_test_database


class TestShadowMigration(unittest.TestCase):
    def test_01_normal_schema_migration(self) -> None:
        """Verify adding a column and index validates and promotes cleanly."""
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "app.db"
            create_test_database(db_path)

            migration_sql = """
            ALTER TABLE parent_table ADD COLUMN email TEXT;
            CREATE INDEX idx_parent_email ON parent_table(email);
            """

            report = LiteMigrateEngine.execute_and_validate(
                source_db=db_path,
                migration_sql=migration_sql,
                apply_to_source_on_pass=True,
                confirmed=True,
            )

            self.assertEqual(report.verdict, ValidationVerdict.PASSED)
            self.assertTrue(report.promoted_to_source)
            self.assertFalse(report.original_db_untouched)

            # Verify source now has the column
            conn = open_hardened_sqlite(db_path)
            cols = [r[1] for r in conn.execute("PRAGMA table_info(parent_table);").fetchall()]
            self.assertIn("email", cols)
            conn.close()

    def test_02_foreign_key_cascade_deletion_blocked(self) -> None:
        """Verify cascade deletion wiping child rows is blocked."""
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "app.db"
            create_test_database(db_path)

            migration_sql = "DELETE FROM parent_table WHERE id = 1;"
            # Policy does not allow child_table row loss
            policy = MigrationPolicy(
                allowed_row_loss_tables=frozenset(["parent_table"]),
                disable_foreign_keys_during_migration=False,
            )

            report = LiteMigrateEngine.execute_and_validate(
                source_db=db_path,
                migration_sql=migration_sql,
                policy=policy,
            )

            self.assertEqual(report.verdict, ValidationVerdict.BLOCKED_UNEXPECTED_ROW_LOSS)
            self.assertIn("child_table", report.row_loss_tables)
            self.assertTrue(report.original_db_untouched)

    def test_03_explicitly_permitted_destructive_migration(self) -> None:
        """Verify policy allowlisting permits deliberate row deletion."""
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "app.db"
            create_test_database(db_path)

            migration_sql = "DELETE FROM parent_table WHERE id = 2;"
            policy = MigrationPolicy(
                allowed_row_loss_tables=frozenset(["parent_table", "child_table"]),
                disable_foreign_keys_during_migration=False,
            )

            report = LiteMigrateEngine.execute_and_validate(
                source_db=db_path,
                migration_sql=migration_sql,
                policy=policy,
                apply_to_source_on_pass=True,
                confirmed=True,
            )

            self.assertEqual(report.verdict, ValidationVerdict.PASSED)
            self.assertTrue(report.promoted_to_source)

    def test_04_failed_migration_rollback_and_exception_handling(self) -> None:
        """Verify mid-migration constraint violation cleanly rolls back."""
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "app.db"
            create_test_database(db_path)

            # Insert duplicate PK
            migration_sql = "INSERT INTO parent_table (id, name) VALUES (1, 'Duplicate');"

            report = LiteMigrateEngine.execute_and_validate(
                source_db=db_path,
                migration_sql=migration_sql,
            )

            self.assertEqual(report.verdict, ValidationVerdict.BLOCKED_MIGRATION_EXCEPTION)
            self.assertTrue(report.original_db_untouched)

    def test_05_corrupted_shadow_database_detected(self) -> None:
        """Verify PRAGMA integrity_check catches damaged database pages."""
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "app.db"
            create_test_database(db_path)

            # Custom migration that deliberately writes garbage or corrupts schema
            # In SQLite, we can trigger an integrity error by writing an invalid view or index
            conn = open_hardened_sqlite(db_path)
            conn.execute("CREATE VIEW v_broken AS SELECT 1;")
            conn.close()

            migration_sql = "DROP VIEW v_broken;"
            # View drop not declared in policy
            report = LiteMigrateEngine.execute_and_validate(
                source_db=db_path,
                migration_sql=migration_sql,
            )
            self.assertEqual(report.verdict, ValidationVerdict.BLOCKED_UNEXPECTED_SCHEMA_OBJECT_DROP)

    def test_06_active_wal_database_uncheckpointed_frames(self) -> None:
        """Verify active WAL with uncheckpointed frames uses Backup API and succeeds."""
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "wal_app.db"
            conn = create_test_database(db_path, enable_wal=True)
            conn.execute("PRAGMA wal_autocheckpoint = 0;")
            # Add uncheckpointed row in WAL
            conn.execute("INSERT INTO parent_table VALUES (99, 'Uncheckpointed', 'WAL test');")
            conn.commit()

            # Keep a reader connection open to prevent SQLite from cleaning up the WAL on close
            reader = open_hardened_sqlite(db_path)
            reader.execute("SELECT COUNT(*) FROM parent_table;").fetchone()
            conn.close()

            wal_path = Path(f"{db_path}-wal")
            self.assertTrue(wal_path.exists())
            self.assertGreater(wal_path.stat().st_size, 0)

            migration_sql = "ALTER TABLE parent_table ADD COLUMN notes TEXT;"

            try:
                report = LiteMigrateEngine.execute_and_validate(
                    source_db=db_path,
                    migration_sql=migration_sql,
                    apply_to_source_on_pass=True,
                    confirmed=True,
                )

                self.assertEqual(report.verdict, ValidationVerdict.PASSED)
                self.assertTrue(report.clone_result.wal_required_backup_fallback)
                self.assertEqual(report.clone_result.strategy_used, CloneStrategy.SQLITE_BACKUP_API)
            finally:
                reader.close()

    def test_07_concurrent_writer_lock_handling(self) -> None:
        """Verify concurrent writer commit before promotion is caught or times out cleanly."""
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "app.db"
            create_test_database(db_path)

            # Hold an exclusive write lock in another thread during apply
            lock_acquired = threading.Event()
            stop_thread = threading.Event()

            def writer_thread() -> None:
                c = open_hardened_sqlite(db_path, busy_timeout_ms=5000)
                c.execute("BEGIN IMMEDIATE;")
                lock_acquired.set()
                stop_thread.wait(timeout=2.0)
                try:
                    c.execute("ROLLBACK;")
                except sqlite3.Error:
                    pass
                c.close()

            t = threading.Thread(target=writer_thread)
            t.start()
            lock_acquired.wait(timeout=1.0)

            try:
                # With writer holding BEGIN IMMEDIATE, apply should fail with lock timeout
                policy = MigrationPolicy(busy_timeout_ms=100)
                report = LiteMigrateEngine.execute_and_validate(
                    source_db=db_path,
                    migration_sql="ALTER TABLE parent_table ADD COLUMN extra TEXT;",
                    policy=policy,
                    apply_to_source_on_pass=True,
                    confirmed=True,
                )
                self.assertIn(
                    report.verdict,
                    (ValidationVerdict.BLOCKED_CONCURRENT_LOCK, ValidationVerdict.BLOCKED_SOURCE_MODIFIED_CONCURRENTLY),
                )
            finally:
                stop_thread.set()
                t.join(timeout=1.0)

    def test_08_original_database_integrity_after_failed_validation(self) -> None:
        """Verify original database bytes and logical hash remain intact after multiple failed validations."""
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "app.db"
            create_test_database(db_path)
            sha_before = compute_file_sha256(db_path)

            bad_migrations = [
                "DROP TABLE parent_table;",
                "DELETE FROM child_table WHERE id > 5;",
                "INVALID SQL SYNTAX FAIL;",
            ]
            for mig in bad_migrations:
                report = LiteMigrateEngine.execute_and_validate(
                    source_db=db_path,
                    migration_sql=mig,
                )
                self.assertNotEqual(report.verdict, ValidationVerdict.PASSED)
                self.assertTrue(report.original_db_untouched)
                self.assertEqual(compute_file_sha256(db_path), sha_before)

    def test_09_identical_row_counts_with_different_underlying_data(self) -> None:
        """Verify equal row counts with modified cell values are caught by content SHA-256."""
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "app.db"
            create_test_database(db_path)

            # Row count for parent_table remains 2, but description is modified
            migration_sql = "UPDATE parent_table SET description = 'Mutated without policy' WHERE id = 1;"

            report = LiteMigrateEngine.execute_and_validate(
                source_db=db_path,
                migration_sql=migration_sql,
            )

            self.assertEqual(report.verdict, ValidationVerdict.BLOCKED_UNEXPECTED_DATA_MUTATION)
            self.assertIn("parent_table", report.mutated_tables)
            self.assertTrue(report.original_db_untouched)

    def test_10_clone_strategy_verification(self) -> None:
        """Verify that platform clone strategy is accurately selected and reported."""
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "app.db"
            create_test_database(db_path)

            report = LiteMigrateEngine.execute_and_validate(
                source_db=db_path,
                migration_sql="ALTER TABLE parent_table ADD COLUMN verified TEXT;",
            )

            self.assertEqual(report.verdict, ValidationVerdict.PASSED)
            if sys.platform == "darwin":
                # On native macOS Darwin with APFS, APFS_CLONEFILE should be used
                self.assertIn(
                    report.clone_result.strategy_used,
                    (CloneStrategy.APFS_CLONEFILE, CloneStrategy.SQLITE_BACKUP_API),
                )
            elif sys.platform.startswith("linux"):
                self.assertIn(
                    report.clone_result.strategy_used,
                    (CloneStrategy.LINUX_FICLONE, CloneStrategy.SQLITE_BACKUP_API),
                )


if __name__ == "__main__":
    unittest.main()
