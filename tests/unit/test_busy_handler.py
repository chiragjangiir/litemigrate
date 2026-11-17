import sqlite3
from litemigrate.busy_handler import configure_busy_timeout

def test_configure_busy_timeout():
    conn = sqlite3.connect(":memory:")
    timeout = configure_busy_timeout(conn, 3000)
    assert timeout == 3000
