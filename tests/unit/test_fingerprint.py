"""Unit tests for fingerprinting, canonical cell bytes, row identity, and column hashes."""

from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from litemigrate.exceptions import UnsupportedTableStructureError
from litemigrate.fingerprint import (
    canonical_cell_bytes,
    fingerprint_table_and_columns,
    get_table_identity_info,
)
from litemigrate.sqlite_backend import open_hardened_sqlite


class TestFingerprint(unittest.TestCase):
    def test_canonical_cell_bytes_types(self) -> None:
        self.assertEqual(canonical_cell_bytes(None), b"N:0:;")
        self.assertEqual(canonical_cell_bytes(True), b"I:1:1;")
        self.assertEqual(canonical_cell_bytes(False), b"I:1:0;")
        self.assertEqual(canonical_cell_bytes(42), b"I:2:42;")
        self.assertEqual(canonical_cell_bytes("hello"), b"T:5:hello;")
        self.assertEqual(canonical_cell_bytes(b"\x00\xff"), b"B:2:\x00\xff;")

    def test_signed_zero_float_discrimination(self) -> None:
        pos_zero = canonical_cell_bytes(+0.0)
        neg_zero = canonical_cell_bytes(-0.0)
        self.assertNotEqual(pos_zero, neg_zero)
        self.assertEqual(pos_zero, b"R:8:0000000000000000;")
        self.assertEqual(neg_zero, b"R:8:8000000000000000;")

    def test_row_identity_binding_catches_row_value_swaps(self) -> None:
        """Proves that swapping values between two rows alters column digests."""
        with tempfile.TemporaryDirectory() as td:
            p1 = Path(td) / "db1.sqlite"
            p2 = Path(td) / "db2.sqlite"

            conn1 = open_hardened_sqlite(p1)
            conn1.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, email TEXT);")
            conn1.execute("INSERT INTO users VALUES (1, 'alice@example.com'), (2, 'bob@example.com');")
            conn1.commit()

            conn2 = open_hardened_sqlite(p2)
            conn2.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, email TEXT);")
            # Swapped values
            conn2.execute("INSERT INTO users VALUES (1, 'bob@example.com'), (2, 'alice@example.com');")
            conn2.commit()

            _, col_hashes1 = fingerprint_table_and_columns(conn1, "users", ("id", "email"))
            _, col_hashes2 = fingerprint_table_and_columns(conn2, "users", ("id", "email"))

            conn1.close()
            conn2.close()

            # Because email values were swapped between id 1 and id 2, the email column digest MUST differ
            self.assertNotEqual(col_hashes1["email"], col_hashes2["email"])

    def test_without_rowid_single_and_composite_pk(self) -> None:
        """Verifies stable fingerprinting on WITHOUT ROWID tables."""
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "test.db"
            conn = open_hardened_sqlite(db_path)
            conn.execute(
                """
                CREATE TABLE composite_test (
                    tenant_id INTEGER,
                    user_id INTEGER,
                    val TEXT,
                    PRIMARY KEY (tenant_id, user_id)
                ) WITHOUT ROWID;
                """
            )
            conn.execute("INSERT INTO composite_test VALUES (1, 10, 'A'), (1, 20, 'B'), (2, 10, 'C');")
            conn.commit()

            has_rowid, pk_cols = get_table_identity_info(conn, "composite_test")
            self.assertFalse(has_rowid)
            self.assertEqual(pk_cols, ("tenant_id", "user_id"))

            t_hash1, col_hashes1 = fingerprint_table_and_columns(
                conn, "composite_test", ("tenant_id", "user_id", "val")
            )

            # Re-running produces identical deterministic hash
            t_hash2, col_hashes2 = fingerprint_table_and_columns(
                conn, "composite_test", ("tenant_id", "user_id", "val")
            )
            self.assertEqual(t_hash1, t_hash2)
            self.assertEqual(col_hashes1, col_hashes2)
            conn.close()

    def test_table_without_rowid_or_pk_raises_error(self) -> None:
        """If a table cannot provide rowid or primary key, raise UnsupportedTableStructureError."""
        mock_conn = sqlite3.connect(":memory:")
        with self.assertRaises(UnsupportedTableStructureError):
            get_table_identity_info(mock_conn, "nonexistent")
        mock_conn.close()

    def test_table_with_user_columns_shadowing_rowid_aliases(self) -> None:
        """Verify handling when user columns shadow rowid, _rowid_, and/or oid."""
        conn = sqlite3.connect(":memory:")

        # 1. User column named 'rowid'
        conn.execute("CREATE TABLE t_rowid (rowid TEXT, data TEXT);")
        conn.execute("INSERT INTO t_rowid VALUES ('user_val', 'content');")
        has_rowid, info = get_table_identity_info(conn, "t_rowid")
        self.assertTrue(has_rowid)
        self.assertEqual(info, ("_rowid_",))
        t_hash, col_hashes = fingerprint_table_and_columns(conn, "t_rowid", ("rowid", "data"))
        self.assertIn("rowid", col_hashes)
        self.assertIn("data", col_hashes)

        # 2. User column named '_rowid_'
        conn.execute("CREATE TABLE t_under_rowid (_rowid_ TEXT, data TEXT);")
        conn.execute("INSERT INTO t_under_rowid VALUES ('custom_id', 'content');")
        has_rowid, info = get_table_identity_info(conn, "t_under_rowid")
        self.assertTrue(has_rowid)
        self.assertEqual(info, ("rowid",))

        # 3. User columns named 'rowid' AND '_rowid_' -> falls back to 'oid'
        conn.execute("CREATE TABLE t_both (rowid TEXT, _rowid_ TEXT, data TEXT);")
        conn.execute("INSERT INTO t_both VALUES ('u1', 'u2', 'content');")
        has_rowid, info = get_table_identity_info(conn, "t_both")
        self.assertTrue(has_rowid)
        self.assertEqual(info, ("oid",))

        # 4. User columns named 'rowid', '_rowid_', and 'oid' with PRIMARY KEY
        conn.execute(
            "CREATE TABLE t_all_shadowed (rowid TEXT, _rowid_ TEXT, oid TEXT, id INT PRIMARY KEY);"
        )
        conn.execute("INSERT INTO t_all_shadowed VALUES ('r', '_r', 'o', 100);")
        has_rowid, info = get_table_identity_info(conn, "t_all_shadowed")
        self.assertFalse(has_rowid)
        self.assertEqual(info, ("id",))

        # 5. User columns named 'rowid', '_rowid_', and 'oid' WITHOUT PRIMARY KEY
        conn.execute("CREATE TABLE t_unusable (rowid TEXT, _rowid_ TEXT, oid TEXT, data TEXT);")
        with self.assertRaises(UnsupportedTableStructureError):
            get_table_identity_info(conn, "t_unusable")

        conn.close()

    def test_empty_table_fingerprinting(self) -> None:
        """Verify empty table produces deterministic hashes without errors."""
        conn = sqlite3.connect(":memory:")
        conn.execute("CREATE TABLE empty_t (id INTEGER PRIMARY KEY, note TEXT);")
        t_hash1, col_hashes1 = fingerprint_table_and_columns(conn, "empty_t", ("id", "note"))
        t_hash2, col_hashes2 = fingerprint_table_and_columns(conn, "empty_t", ("id", "note"))
        self.assertEqual(t_hash1, t_hash2)
        self.assertEqual(col_hashes1, col_hashes2)
        self.assertIn("id", col_hashes1)
        self.assertIn("note", col_hashes1)
        conn.close()

    def test_null_and_duplicate_values_determinism(self) -> None:
        """Verify tables with NULLs and identical duplicate values hash deterministically."""
        conn = sqlite3.connect(":memory:")
        conn.execute("CREATE TABLE dup_t (id INTEGER PRIMARY KEY, val TEXT);")
        conn.execute("INSERT INTO dup_t VALUES (1, NULL), (2, NULL), (3, 'dup'), (4, 'dup');")
        t_hash1, col_hashes1 = fingerprint_table_and_columns(conn, dup_t := "dup_t", ("id", "val"))
        t_hash2, col_hashes2 = fingerprint_table_and_columns(conn, "dup_t", ("id", "val"))
        self.assertEqual(t_hash1, t_hash2)
        self.assertEqual(col_hashes1, col_hashes2)
        conn.close()


if __name__ == "__main__":
    unittest.main()
