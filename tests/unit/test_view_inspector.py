import sqlite3
from litemigrate.view_inspector import list_views

def test_list_views():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE items (id INT, val TEXT);")
    conn.execute("CREATE VIEW active_items AS SELECT * FROM items WHERE id > 0;")
    views = list_views(conn)
    assert len(views) == 1
    assert views[0]["name"] == "active_items"
