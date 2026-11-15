import unittest
from litemigrate.sql_splitter import split_sql_statements

class TestSqlSplitter(unittest.TestCase):
    def test_splits_multiple_statements(self):
        sql = "CREATE TABLE a (id INT); INSERT INTO a VALUES (1);"
        stmts = split_sql_statements(sql)
        self.assertEqual(len(stmts), 2)
        self.assertEqual(stmts[0], "CREATE TABLE a (id INT)")
        self.assertEqual(stmts[1], "INSERT INTO a VALUES (1)")

    def test_preserves_semicolons_inside_quotes(self):
        sql = "INSERT INTO a VALUES ('hello;world'); SELECT 1;"
        stmts = split_sql_statements(sql)
        self.assertEqual(len(stmts), 2)
        self.assertEqual(stmts[0], "INSERT INTO a VALUES ('hello;world')")
        self.assertEqual(stmts[1], "SELECT 1")
