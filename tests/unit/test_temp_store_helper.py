import sqlite3
from litemigrate.temp_store_helper import configure_temp_store_memory

def test_temp_store_memory():
    conn = sqlite3.connect(":memory:")
    val = configure_temp_store_memory(conn)
    assert val == 2 # 2 = MEMORY
