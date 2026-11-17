import sqlite3
from litemigrate.cache_size_helper import get_cache_size

def test_get_cache_size():
    conn = sqlite3.connect(":memory:")
    cs = get_cache_size(conn)
    assert isinstance(cs, int)
