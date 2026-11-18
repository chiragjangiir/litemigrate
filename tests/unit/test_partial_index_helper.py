from litemigrate.partial_index_helper import build_partial_index_sql

def test_build_partial_index():
    sql = build_partial_index_sql("idx_active_users", "users", ["email"], "status = 'active'")
    assert sql == "CREATE INDEX idx_active_users ON users (email) WHERE status = 'active';"
