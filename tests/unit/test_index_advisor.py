from litemigrate.index_advisor import suggest_index_name

def test_suggest_index_name():
    name = suggest_index_name("orders", ["user_id", "status"])
    assert name == "idx_orders_user_id_status"
