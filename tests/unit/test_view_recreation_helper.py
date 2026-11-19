import sqlite3
from litemigrate.view_recreation_helper import ViewRecreationHelper

def test_view_recreation():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE t (x INT)")
    conn.execute("CREATE VIEW v_t AS SELECT x * 2 FROM t")
    views = ViewRecreationHelper.extract_views(conn)
    assert len(views) == 1
    ViewRecreationHelper.drop_views(conn, views)
    assert len(ViewRecreationHelper.extract_views(conn)) == 0
    ViewRecreationHelper.restore_views(conn, views)
    assert len(ViewRecreationHelper.extract_views(conn)) == 1
