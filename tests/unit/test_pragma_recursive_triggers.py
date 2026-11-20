import sqlite3
from litemigrate.pragma_recursive_triggers import PragmaRecursiveTriggers

def test_recursive_triggers():
    conn = sqlite3.connect(":memory:")
    PragmaRecursiveTriggers.set_status(conn, True)
    assert PragmaRecursiveTriggers.get_status(conn) is True
    PragmaRecursiveTriggers.set_status(conn, False)
    assert PragmaRecursiveTriggers.get_status(conn) is False
