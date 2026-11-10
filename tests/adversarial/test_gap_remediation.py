"""Regression test suite for verified engineering gaps (Gaps A, B, and F)."""

from __future__ import annotations

import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

from litemigrate.cloning import try_apfs_clonefile
from litemigrate.engine import LiteMigrateEngine
from litemigrate.exceptions import (
    UnsupportedMigrationTypeError,
)
from litemigrate.fingerprint import (
    fingerprint_table_and_columns,
)
from litemigrate.models import ValidationVerdict
from litemigrate.promotion import promote_shadow_to_source
from litemigrate.sqlite_backend import open_hardened_sqlite
from tests.fixtures.database_setup import create_test_database


class TestGapRemediation(unittest.TestCase):
    # -------------------------------------------------------------
    # GAP A: Callable migration handling
    # -------------------------------------------------------------
    def test_callable_migration_is_explicitly_rejected_in_public_api(self) -> None:
        """Gap A: Passing a callable to the public engine returns BLOCKED_UNSUPPORTED_MIGRATION_TYPE."""
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "app.db"
            create_test_database(db_path)

            executed = []

            def dangerous_callable(conn: sqlite3.Connection) -> None:
                executed.append("ran")
                conn.execute("DROP TABLE parent_table;")

            report = LiteMigrateEngine.execute_and_validate(
                source_db=db_path,
                migration_sql=dangerous_callable,  # type: ignore[arg-type]
                apply_to_source_on_pass=True,
                confirmed=True,
            )

            self.assertEqual(report.verdict, ValidationVerdict.BLOCKED_UNSUPPORTED_MIGRATION_TYPE)
            self.assertEqual(len(executed), 0, "Dangerous callable must NEVER be invoked!")
            self.assertTrue(report.original_db_untouched)

            # Verify source database is intact
            conn = open_hardened_sqlite(db_path)
            tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()]
            self.assertIn("parent_table", tables)
            conn.close()

    def test_callable_migration_rejected_in_promotion(self) -> None:
        """Gap A: promote_shadow_to_source directly raises UnsupportedMigrationTypeError for callables."""
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "app.db"
            create_test_database(db_path)

            def dummy_callable(conn: sqlite3.Connection) -> None:
                pass

            with self.assertRaises(UnsupportedMigrationTypeError):
                promote_shadow_to_source(
                    shadow_path=Path(td) / "shadow",
                    source_path=db_path,
                    expected_source_digest="digest",
                    migration_sql=dummy_callable,  # type: ignore[arg-type]
                )

    # -------------------------------------------------------------
    # GAP B: Data fingerprint correctness & Canonical Row Identity
    # -------------------------------------------------------------
    def test_rowid_mutation_detected_even_if_cell_values_identical(self) -> None:
        """Gap B: Modifying rowid alters table and column digests even if cell data is identical."""
        with tempfile.TemporaryDirectory() as td:
            p1 = Path(td) / "db1.sqlite"
            p2 = Path(td) / "db2.sqlite"

            conn1 = open_hardened_sqlite(p1)
            conn1.execute("CREATE TABLE items (id INTEGER, val TEXT);")
            conn1.execute("INSERT INTO items VALUES (1, 'apple'), (2, 'banana');")
            conn1.commit()

            conn2 = open_hardened_sqlite(p2)
            conn2.execute("CREATE TABLE items (id INTEGER, val TEXT);")
            conn2.execute("INSERT INTO items VALUES (1, 'apple'), (2, 'banana');")
            # Mutate rowid on db2
            conn2.execute("UPDATE items SET rowid = rowid + 100 WHERE id = 1;")
            conn2.commit()

            t_hash1, col_hashes1 = fingerprint_table_and_columns(conn1, "items", ("id", "val"))
            t_hash2, col_hashes2 = fingerprint_table_and_columns(conn2, "items", ("id", "val"))

            conn1.close()
            conn2.close()

            self.assertNotEqual(t_hash1, t_hash2)
            self.assertNotEqual(col_hashes1["val"], col_hashes2["val"])

    def test_without_rowid_composite_pk_value_swap_detected(self) -> None:
        """Gap B: Swapping values in WITHOUT ROWID table with composite PK alters column hashes."""
        with tempfile.TemporaryDirectory() as td:
            p1 = Path(td) / "db1.sqlite"
            p2 = Path(td) / "db2.sqlite"

            conn1 = open_hardened_sqlite(p1)
            conn1.execute(
                """
                CREATE TABLE account_balances (
                    org_id INTEGER,
                    account_id INTEGER,
                    balance INTEGER,
                    PRIMARY KEY (org_id, account_id)
                ) WITHOUT ROWID;
                """
            )
            conn1.execute("INSERT INTO account_balances VALUES (1, 100, 5000), (1, 200, 9000);")
            conn1.commit()

            conn2 = open_hardened_sqlite(p2)
            conn2.execute(
                """
                CREATE TABLE account_balances (
                    org_id INTEGER,
                    account_id INTEGER,
                    balance INTEGER,
                    PRIMARY KEY (org_id, account_id)
                ) WITHOUT ROWID;
                """
            )
            # Swapped balances
            conn2.execute("INSERT INTO account_balances VALUES (1, 100, 9000), (1, 200, 5000);")
            conn2.commit()

            t1, c1 = fingerprint_table_and_columns(conn1, "account_balances", ("org_id", "account_id", "balance"))
            t2, c2 = fingerprint_table_and_columns(conn2, "account_balances", ("org_id", "account_id", "balance"))

            conn1.close()
            conn2.close()

            self.assertNotEqual(t1, t2)
            self.assertNotEqual(c1["balance"], c2["balance"])

    # -------------------------------------------------------------
    # GAP F: Native APFS clonefile verification on macOS
    # -------------------------------------------------------------
    def test_native_darwin_apfs_clonefile(self) -> None:
        """Gap F: Test native macOS APFS clonefile execution directly on Darwin host."""
        if sys.platform != "darwin":
            self.skipTest("APFS clonefile(2) test is Darwin-specific.")

        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "source.db"
            dst = Path(td) / "shadow.db"
            conn = create_test_database(src)
            conn.close()

            try_apfs_clonefile(src, dst)

            self.assertTrue(dst.exists())
            self.assertEqual(src.stat().st_size, dst.stat().st_size)
            mode = os.stat(dst).st_mode & 0o777
            self.assertEqual(mode, 0o600)


if __name__ == "__main__":
    unittest.main()
