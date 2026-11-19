from litemigrate.table_column_order_diff import TableColumnOrderDiff

def test_column_order_diff():
    assert TableColumnOrderDiff.order_matches(["id", "name"], ["ID", "name"]) is True
    assert TableColumnOrderDiff.order_matches(["id", "name"], ["name", "id"]) is False
