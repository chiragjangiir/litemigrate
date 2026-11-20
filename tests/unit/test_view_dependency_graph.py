from litemigrate.view_dependency_graph import ViewDependencyGraph

def test_view_dependency_graph():
    sql = "CREATE VIEW v_active AS SELECT * FROM users JOIN orders ON users.id = orders.user_id"
    tables = {"users", "orders", "products"}
    deps = ViewDependencyGraph.extract_dependencies(sql, tables)
    assert deps == ["orders", "users"]
