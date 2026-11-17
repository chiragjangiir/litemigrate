import sqlite3
from litemigrate.encoding_detector import get_database_encoding

def test_database_encoding():
    conn = sqlite3.connect(":memory:")
    enc = get_database_encoding(conn)
    assert "UTF" in enc
