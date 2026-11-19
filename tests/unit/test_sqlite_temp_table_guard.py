import sqlite3
from litemigrate.sqlite_temp_table_guard import SqliteTempTableGuard

def test_temp_table_guard():
    conn = sqlite3.connect(":memory:")
    with SqliteTempTableGuard.create_temp_table(conn, "tmp_stage", "id INT, val TEXT") as t_name:
        conn.execute(f"INSERT INTO {t_name} VALUES (1, 'ok')")
        cnt = conn.execute(f"SELECT COUNT(*) FROM {t_name}").fetchone()[0]
        assert cnt == 1
    tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_temp_master WHERE type='table'").fetchall()]
    assert "tmp_stage" not in tables
