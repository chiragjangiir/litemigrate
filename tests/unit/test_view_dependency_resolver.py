from litemigrate.view_dependency_resolver import extract_view_referenced_tables

def test_extract_tables():
    sql = "CREATE VIEW my_view AS SELECT u.id FROM users u JOIN orders o ON u.id = o.user_id;"
    tables = extract_view_referenced_tables(sql)
    assert "users" in tables
    assert "orders" in tables
