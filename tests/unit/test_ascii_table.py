import unittest
from litemigrate.ascii_table import format_ascii_table

class TestAsciiTable(unittest.TestCase):
    def test_format_table(self):
        table = format_ascii_table(["Col A", "Col B"], [["1", "Alice"], ["200", "Bob"]])
        self.assertIn("| Col A | Col B |", table)
        self.assertIn("| 1     | Alice |", table)
        self.assertIn("| 200   | Bob   |", table)
