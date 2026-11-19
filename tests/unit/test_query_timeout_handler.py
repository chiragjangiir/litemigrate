import sqlite3
from litemigrate.query_timeout_handler import QueryTimeoutHandler

def test_query_timeout_install():
    conn = sqlite3.connect(":memory:")
    QueryTimeoutHandler.set_timeout(conn, 5.0)
    cur = conn.cursor()
    assert cur.execute("SELECT 1").fetchone()[0] == 1
    QueryTimeoutHandler.clear_timeout(conn)
