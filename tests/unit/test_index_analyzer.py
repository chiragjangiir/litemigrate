import unittest
import sqlite3
from litemigrate.index_analyzer import analyze_table_indexes

class TestIndexAnalyzer(unittest.TestCase):
    def test_analyzes_table_indexes(self):
        conn = sqlite3.connect(":memory:")
        conn.execute("CREATE TABLE users (id INT, email TEXT);")
        conn.execute("CREATE INDEX idx_users_email ON users(email);")
        indexes = analyze_table_indexes(conn, "users")
        self.assertIn("idx_users_email", indexes)
        conn.close()
