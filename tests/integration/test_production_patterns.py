import unittest
import tempfile
import sqlite3
from pathlib import Path
from litemigrate.engine import LiteMigrateEngine
from litemigrate.models import ValidationVerdict
from litemigrate.policy import MigrationPolicy


class TestProductionPatterns(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "prod_patterns.db"
        self.patterns_dir = Path(__file__).resolve().parent.parent.parent / "examples" / "production_patterns"

        conn = sqlite3.connect(str(self.db_path))
        conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, tenant_id INTEGER, email TEXT);")
        conn.execute("INSERT INTO users VALUES (1, 100, 'alice@example.com'), (2, 100, 'bob@example.com');")
        conn.execute("CREATE TABLE subscriptions (id INTEGER PRIMARY KEY, user_id INTEGER, plan_tier TEXT, status TEXT, created_at DATETIME);")
        conn.execute("INSERT INTO subscriptions VALUES (1, 1, 'starter', 'active', '2026-01-01');")
        conn.commit()
        conn.close()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_composite_unique_index(self):
        sql_file = self.patterns_dir / "004_composite_unique_index.sql"
        report = LiteMigrateEngine.execute_and_validate(
            source_db=self.db_path,
            migration_sql=sql_file,
        )
        self.assertEqual(report.verdict, ValidationVerdict.PASSED)

    def test_enum_check_constraint_migration(self):
        sql_file = self.patterns_dir / "005_enum_check_constraint_migration.sql"
        policy = MigrationPolicy(allowed_dropped_tables=["subscriptions"])
        report = LiteMigrateEngine.execute_and_validate(
            source_db=self.db_path,
            migration_sql=sql_file,
            policy=policy,
        )
        self.assertEqual(report.verdict, ValidationVerdict.PASSED)


if __name__ == "__main__":
    unittest.main()
