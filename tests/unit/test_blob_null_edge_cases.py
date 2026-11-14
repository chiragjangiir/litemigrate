import unittest
import tempfile
import sqlite3
from pathlib import Path
from litemigrate.fingerprint import fingerprint_table_and_columns


class TestBlobNullEdgeCases(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "edge_case.db"
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, val BLOB);")

    def tearDown(self):
        self.conn.close()
        self.temp_dir.cleanup()

    def test_empty_blob_vs_empty_string_vs_null(self):
        # 1. Insert NULL
        self.conn.execute("INSERT INTO t VALUES (1, NULL);")
        self.conn.commit()
        table_hash_null, col_hash_null = fingerprint_table_and_columns(self.conn, "t", ["id", "val"])

        # 2. Update to empty string
        self.conn.execute("UPDATE t SET val = '' WHERE id = 1;")
        self.conn.commit()
        table_hash_str, col_hash_str = fingerprint_table_and_columns(self.conn, "t", ["id", "val"])

        # 3. Update to empty blob
        self.conn.execute("UPDATE t SET val = zeroblob(0) WHERE id = 1;")
        self.conn.commit()
        table_hash_blob, col_hash_blob = fingerprint_table_and_columns(self.conn, "t", ["id", "val"])

        # Distinct data states must produce distinct fingerprints
        self.assertNotEqual(table_hash_null, table_hash_str)
        self.assertNotEqual(table_hash_null, table_hash_blob)
        self.assertNotEqual(col_hash_null["val"], col_hash_str["val"])
        self.assertNotEqual(col_hash_null["val"], col_hash_blob["val"])


if __name__ == "__main__":
    unittest.main()
