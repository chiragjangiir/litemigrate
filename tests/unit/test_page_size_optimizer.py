import sqlite3
from litemigrate.page_size_optimizer import get_page_size

def test_get_page_size():
    conn = sqlite3.connect(":memory:")
    size = get_page_size(conn)
    assert size in (1024, 2048, 4096, 8192, 16384, 32768, 65536)
