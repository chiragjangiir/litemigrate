"""Integration tests for foreign-key cascade wipe reproduction (ariga/atlas #3317) and 12-step rebuilds."""

from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from litemigrate.engine import LiteMigrateEngine
from litemigrate.models import ValidationVerdict
from litemigrate.policy import MigrationPolicy
from tests.fixtures.database_setup import create_test_database


class TestForeignKeyCascade(unittest.TestCase):
    def test_pragma_foreign_keys_is_noop_inside_transaction(self) -> None:
        """Verifies SQLite's documented behavior: PRAGMA foreign_keys is ignored inside a transaction."""
        conn = sqlite3.connect(":memory:")
        conn.execute("PRAGMA foreign_keys = ON;")
        self.assertEqual(conn.execute("PRAGMA foreign_keys;").fetchone()[0], 1)

        conn.execute("BEGIN TRANSACTION;")
        conn.execute("PRAGMA foreign_keys = OFF;")
        # Still 1 because PRAGMA foreign_keys cannot be changed inside a transaction!
        self.assertEqual(conn.execute("PRAGMA foreign_keys;").fetchone()[0], 1)
        conn.execute("COMMIT;")
        conn.close()

    def test_atlas_3317_bug_reproduction_caught_by_shadow_auditor(self) -> None:
        """Reproduce ariga/atlas #3317: dropping parent table with foreign_keys=ON wipes child rows."""
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "test.db"
            create_test_database(db_path)

            # Faulty migration that drops parent_table without turning off foreign_keys
            # before transaction or table rebuild
            migration_sql = """
            DROP TABLE parent_table;
            CREATE TABLE parent_table (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                new_col TEXT
            );
            """
            # Policy allows dropping parent_table, but NOT child_table row loss!
            policy = MigrationPolicy(
                allowed_dropped_tables=frozenset(["parent_table"]),
                disable_foreign_keys_during_migration=False,  # Emulates Atlas bug where FKs remain ON
            )

            report = LiteMigrateEngine.execute_and_validate(
                source_db=db_path,
                migration_sql=migration_sql,
                policy=policy,
            )

            # Auditor must block this because child_table lost all 40 rows!
            self.assertEqual(report.verdict, ValidationVerdict.BLOCKED_UNEXPECTED_ROW_LOSS)
            self.assertIn("child_table", report.row_loss_tables)
            self.assertTrue(report.original_db_untouched)

    def test_dangling_foreign_key_detected_after_rebuild(self) -> None:
        """Verify orphan foreign keys after table rebuild trigger BLOCKED_FOREIGN_KEY_VIOLATION."""
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "test.db"
            create_test_database(db_path)

            # Rebuild parent table with only ID 1, leaving child rows referencing parent ID 2 dangling!
            migration_sql = """
            CREATE TABLE parent_new (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL
            );
            INSERT INTO parent_new (id, name) SELECT id, name FROM parent_table WHERE id = 1;
            DROP TABLE parent_table;
            ALTER TABLE parent_new RENAME TO parent_table;
            """
            policy = MigrationPolicy(
                allowed_dropped_tables=frozenset(["parent_table"]),
                allowed_row_loss_tables=frozenset(["parent_table"]),
                disable_foreign_keys_during_migration=True,
            )

            report = LiteMigrateEngine.execute_and_validate(
                source_db=db_path,
                migration_sql=migration_sql,
                policy=policy,
            )

            self.assertEqual(report.verdict, ValidationVerdict.BLOCKED_FOREIGN_KEY_VIOLATION)
            self.assertTrue(len(report.foreign_key_violations) > 0)
            self.assertTrue(report.original_db_untouched)

    def test_safe_12_step_parent_rebuild_preserves_child_rows(self) -> None:
        """Verify that a proper 12-step rebuild preserving all parent rows passes validation."""
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "test.db"
            create_test_database(db_path)

            migration_sql = """
            CREATE TABLE parent_new (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'active'
            );
            INSERT INTO parent_new (id, name, description)
                SELECT id, name, description FROM parent_table;
            DROP TABLE parent_table;
            ALTER TABLE parent_new RENAME TO parent_table;
            """
            policy = MigrationPolicy(
                allowed_dropped_tables=frozenset(["parent_table"]),
                disable_foreign_keys_during_migration=True,
            )

            report = LiteMigrateEngine.execute_and_validate(
                source_db=db_path,
                migration_sql=migration_sql,
                policy=policy,
            )

            self.assertEqual(report.verdict, ValidationVerdict.PASSED)
            self.assertEqual(report.tables_after["child_table"].row_count, 40)
            self.assertEqual(report.tables_after["parent_table"].row_count, 2)


if __name__ == "__main__":
    unittest.main()
