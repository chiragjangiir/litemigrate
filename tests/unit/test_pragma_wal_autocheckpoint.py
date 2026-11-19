import sqlite3
from litemigrate.pragma_wal_autocheckpoint import PragmaWalAutocheckpoint

def test_wal_autocheckpoint():
    conn = sqlite3.connect(":memory:")
    val = PragmaWalAutocheckpoint.get_checkpoint_pages(conn)
    assert val == 1000
    new_val = PragmaWalAutocheckpoint.set_checkpoint_pages(conn, 2000)
    assert new_val == 2000
