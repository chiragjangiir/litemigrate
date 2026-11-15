import unittest
import tempfile
import sqlite3
from pathlib import Path
from litemigrate.engine import LiteMigrateEngine
from litemigrate.models import ValidationVerdict

class TestTriggerPatterns(unittest.TestCase):
    def test_trigger_audit_migration(self):
        temp_dir = tempfile.TemporaryDirectory()
        db_path = Path(temp_dir.name) / "test.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute("CREATE TABLE users (id INT, name TEXT);")
        conn.commit()
        conn.close()

        sql_file = Path(__file__).resolve().parent.parent.parent / "examples" / "advanced_patterns" / "008_trigger_audit_log.sql"
        report = LiteMigrateEngine.execute_and_validate(source_db=db_path, migration_sql=sql_file)
        self.assertEqual(report.verdict, ValidationVerdict.PASSED)
        temp_dir.cleanup()
