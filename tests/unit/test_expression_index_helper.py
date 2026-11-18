from litemigrate.expression_index_helper import build_expression_index_sql

def test_build_expression_index():
    sql = build_expression_index_sql("idx_lower_email", "users", "lower(email)")
    assert sql == "CREATE INDEX idx_lower_email ON users (lower(email));"
