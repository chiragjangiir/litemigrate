import sqlite3
from litemigrate.schema_version_reader import get_user_version, set_user_version

def test_user_version():
    conn = sqlite3.connect(":memory:")
    assert get_user_version(conn) == 0
    set_user_version(conn, 42)
    assert get_user_version(conn) == 42
