from litemigrate.upsert_generator import build_upsert_sql

def test_build_upsert():
    sql = build_upsert_sql("stats", ["id"], ["views", "clicks"])
    assert "ON CONFLICT (id) DO UPDATE SET views = excluded.views, clicks = excluded.clicks" in sql
