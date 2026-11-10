"""Integration tests for the litemigrate CLI commands."""

from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

from litemigrate.cli import main
from tests.fixtures.database_setup import create_test_database


class TestCli(unittest.TestCase):
    def test_cli_inspect_human_and_json(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "app.db"
            create_test_database(db_path)

            # Human output
            code = main(["inspect", "--db", str(db_path)])
            self.assertEqual(code, 0)

            # JSON output
            old_stdout = sys.stdout
            try:
                sys.stdout = io.StringIO()
                code_json = main(["inspect", "--db", str(db_path), "--json"])
                self.assertEqual(code_json, 0)
                data = json.loads(sys.stdout.getvalue())
                self.assertEqual(data["table_count"], 2)
                self.assertTrue(data["integrity_ok"])
            finally:
                sys.stdout = old_stdout

    def test_cli_validate_safe_migration(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "app.db"
            create_test_database(db_path)

            mig_path = Path(td) / "001.sql"
            mig_path.write_text("ALTER TABLE parent_table ADD COLUMN notes TEXT;")

            code = main(["validate", "--db", str(db_path), "--migration", str(mig_path)])
            self.assertEqual(code, 0)

    def test_cli_validate_unsafe_migration_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "app.db"
            create_test_database(db_path)

            mig_path = Path(td) / "bad.sql"
            mig_path.write_text("DELETE FROM parent_table WHERE id = 1;")

            code = main(["validate", "--db", str(db_path), "--migration", str(mig_path)])
            self.assertEqual(code, 1)

    def test_cli_apply_unconfirmed_in_non_tty_returns_code_4(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "app.db"
            create_test_database(db_path)

            mig_path = Path(td) / "001.sql"
            mig_path.write_text("ALTER TABLE parent_table ADD COLUMN notes TEXT;")

            from unittest.mock import patch
            with patch.object(sys.stdin, "isatty", return_value=False):
                code = main(["apply", "--db", str(db_path), "--migration", str(mig_path)])
                self.assertEqual(code, 4)

    def test_cli_apply_confirmed_applies_and_creates_backup(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "app.db"
            create_test_database(db_path)

            mig_path = Path(td) / "001.sql"
            mig_path.write_text("ALTER TABLE parent_table ADD COLUMN notes TEXT;")
            report_out = Path(td) / "report.json"

            code = main([
                "apply",
                "--db", str(db_path),
                "--migration", str(mig_path),
                "--confirm",
                "--output", str(report_out),
            ])
            self.assertEqual(code, 0)
            self.assertTrue(report_out.exists())

            # Test report command on the output
            code_rep = main(["report", "--input", str(report_out)])
            self.assertEqual(code_rep, 0)


if __name__ == "__main__":
    unittest.main()
