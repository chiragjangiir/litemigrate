import unittest
import sqlite3
from litemigrate.health import check_database_health

class TestHealth(unittest.TestCase):
    def test_quick_check_passes_on_healthy_db(self):
        conn = sqlite3.connect(":memory:")
        ok, msg = check_database_health(conn)
        self.assertTrue(ok)
        self.assertEqual(msg, "ok")
        conn.close()
