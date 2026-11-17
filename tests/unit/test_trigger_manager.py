import sqlite3
from litemigrate.trigger_manager import list_triggers

def test_list_triggers():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE t (x INT);")
    conn.execute("CREATE TRIGGER t_trig AFTER INSERT ON t BEGIN SELECT 1; END;")
    trigs = list_triggers(conn)
    assert len(trigs) == 1
    assert trigs[0]["name"] == "t_trig"
