import unittest
from litemigrate.sanitizer import strip_sql_comments

class TestSanitizer(unittest.TestCase):
    def test_strip_comments(self):
        sql = """-- header comment
        SELECT * FROM users; /* inline comment */
        -- footer
        """
        cleaned = strip_sql_comments(sql)
        self.assertNotIn("header comment", cleaned)
        self.assertNotIn("inline comment", cleaned)
        self.assertIn("SELECT * FROM users;", cleaned)
