import unittest
import tempfile
import sqlite3
from pathlib import Path
from litemigrate.engine import LiteMigrateEngine
from litemigrate.models import ValidationVerdict
from litemigrate.policy import MigrationPolicy


class TestAdvancedMigrationExamples(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "production.db"
        self.examples_dir = Path(__file__).resolve().parent.parent.parent / "examples" / "advanced_migrations"

        conn = sqlite3.connect(str(self.db_path))
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT);")
        conn.execute("CREATE TABLE orders (id INTEGER PRIMARY KEY, user_id INTEGER, total_cents INTEGER, status TEXT, created_at DATETIME);")
        conn.execute("CREATE TABLE products (id INTEGER PRIMARY KEY, sku TEXT, status TEXT, stock_count INTEGER);")
        conn.execute("CREATE TABLE events (id INTEGER PRIMARY KEY, event_type TEXT, payload TEXT);")

        conn.execute("INSERT INTO users VALUES (1, 'Alice');")
        conn.execute("INSERT INTO orders VALUES (101, 1, 4500, 'completed', '2026-01-01');")
        conn.execute("INSERT INTO products VALUES (1, 'ABCD-1234', 'active', 50);")
        conn.execute("INSERT INTO events VALUES (1, 'login', '{\"ip\": \"127.0.0.1\"}');")
        conn.commit()
        conn.close()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_rebuild_table_fk_cascade(self):
        sql_file = self.examples_dir / "001_rebuild_table_fk_cascade.sql"
        policy = MigrationPolicy(allowed_dropped_tables=["orders"])
        report = LiteMigrateEngine.execute_and_validate(
            source_db=self.db_path,
            migration_sql=sql_file,
            policy=policy,
        )
        self.assertEqual(report.verdict, ValidationVerdict.PASSED)
        self.assertTrue(report.original_db_untouched)

    def test_generated_columns_partial_index(self):
        sql_file = self.examples_dir / "002_generated_columns_partial_index.sql"
        report = LiteMigrateEngine.execute_and_validate(
            source_db=self.db_path,
            migration_sql=sql_file,
        )
        self.assertEqual(report.verdict, ValidationVerdict.PASSED)

    def test_partitioned_views(self):
        sql_file = self.examples_dir / "003_partitioned_views.sql"
        report = LiteMigrateEngine.execute_and_validate(
            source_db=self.db_path,
            migration_sql=sql_file,
        )
        self.assertEqual(report.verdict, ValidationVerdict.PASSED)


if __name__ == "__main__":
    unittest.main()
