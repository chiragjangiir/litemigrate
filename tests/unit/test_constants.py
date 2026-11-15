import unittest
from litemigrate.constants import ERROR_DESCRIPTIONS, SQLITE_BUSY

class TestConstants(unittest.TestCase):
    def test_error_description(self):
        self.assertIn("acquire database lock", ERROR_DESCRIPTIONS[SQLITE_BUSY])
