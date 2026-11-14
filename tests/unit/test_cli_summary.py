import unittest
import tempfile
import sqlite3
from pathlib import Path
from litemigrate.cli import main


class TestCliSummary(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test.db"
        self.sql_path = Path(self.temp_dir.name) / "001.sql"

        conn = sqlite3.connect(str(self.db_path))
        conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT);")
        conn.execute("INSERT INTO users VALUES (1, 'Alice');")
        conn.commit()
        conn.close()

        self.sql_path.write_text("CREATE TABLE orders (id INTEGER PRIMARY KEY);")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_validate_with_summary_flag(self):
        import io
        from contextlib import redirect_stdout

        buf = io.StringIO()
        with redirect_stdout(buf):
            exit_code = main(["validate", "--db", str(self.db_path), "--migration", str(self.sql_path), "--summary"])
        self.assertEqual(exit_code, 0)
        output = buf.getvalue()
        self.assertIn("LiteMigrate Execution Summary", output)
        self.assertIn("Verdict:       passed", output)


if __name__ == "__main__":
    unittest.main()
