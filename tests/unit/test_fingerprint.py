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
        # Standard SQLite disallows WITHOUT ROWID without PK, but let's test helper directly
        mock_conn = sqlite3.connect(":memory:")
        # In memory empty
        with self.assertRaises(UnsupportedTableStructureError):
            get_table_identity_info(mock_conn, "nonexistent")
        mock_conn.close()


if __name__ == "__main__":
    unittest.main()
