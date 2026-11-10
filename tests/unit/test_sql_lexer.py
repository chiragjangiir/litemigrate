"""Unit tests for the complete_statement SQL splitter and comment stripper."""

from __future__ import annotations

import unittest

from litemigrate.sqlite_backend import split_sql_statements


class TestSqlLexer(unittest.TestCase):
    def test_single_statement(self) -> None:
        stmts = split_sql_statements("CREATE TABLE t (id INT);")
        self.assertEqual(len(stmts), 1)
        self.assertEqual(stmts[0], "CREATE TABLE t (id INT);")

    def test_multiple_statements_on_single_line(self) -> None:
        raw = "ALTER TABLE t ADD COLUMN a INT; ALTER TABLE t ADD COLUMN b INT;"
        stmts = split_sql_statements(raw)
        self.assertEqual(len(stmts), 2)
        self.assertEqual(stmts[0], "ALTER TABLE t ADD COLUMN a INT;")
        self.assertEqual(stmts[1], "ALTER TABLE t ADD COLUMN b INT;")

    def test_leading_comments_and_blank_lines(self) -> None:
        raw = """
        -- Migration 001: Add index
        -- Author: Test
        CREATE INDEX idx_t ON t(a);

        -- Follow-up statement
        UPDATE t SET a = 1;
        """
        stmts = split_sql_statements(raw)
        self.assertEqual(len(stmts), 2)
        self.assertTrue(stmts[0].startswith("CREATE INDEX"))
        self.assertTrue(stmts[1].startswith("UPDATE t"))

    def test_trigger_begin_end_block_not_split(self) -> None:
        raw = """
        CREATE TRIGGER trg_test AFTER INSERT ON t
        BEGIN
            UPDATE stats SET count = count + 1;
            INSERT INTO logs (msg) VALUES ('inserted');
        END;
        """
        stmts = split_sql_statements(raw)
        self.assertEqual(len(stmts), 1)
        self.assertTrue(stmts[0].startswith("CREATE TRIGGER"))
        self.assertTrue(stmts[0].endswith("END;"))


if __name__ == "__main__":
    unittest.main()
