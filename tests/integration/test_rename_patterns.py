import unittest
import tempfile
import sqlite3
from pathlib import Path
from litemigrate.engine import LiteMigrateEngine
from litemigrate.models import ValidationVerdict
from litemigrate.policy import MigrationPolicy

class TestRenamePatterns(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "rename.db"
        self.patterns_dir = Path(__file__).resolve().parent.parent.parent / "examples" / "advanced_patterns"

        conn = sqlite3.connect(str(self.db_path))
        conn.execute("CREATE TABLE members (id INTEGER PRIMARY KEY, legacy_name TEXT, email TEXT UNIQUE);")
        conn.execute("INSERT INTO members VALUES (1, 'Jane Doe', 'jane@example.com');")
        conn.commit()
        conn.close()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_column_rename(self):
        sql_file = self.patterns_dir / "006_zero_downtime_rename.sql"
        policy = MigrationPolicy(allowed_dropped_tables=["members"])
        report = LiteMigrateEngine.execute_and_validate(
            source_db=self.db_path,
            migration_sql=sql_file,
            policy=policy,
        )
        self.assertEqual(report.verdict, ValidationVerdict.PASSED)

    def test_reindex(self):
        sql_file = self.patterns_dir / "007_table_reindex_vacuum.sql"
        report = LiteMigrateEngine.execute_and_validate(
            source_db=self.db_path,
            migration_sql=sql_file,
        )
        self.assertEqual(report.verdict, ValidationVerdict.PASSED)
