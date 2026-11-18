from litemigrate.query_parameter_binder import count_query_placeholders

def test_count_placeholders():
    assert count_query_placeholders("SELECT * FROM t WHERE a = ? AND b = ?;") == 2
    assert count_query_placeholders("SELECT 'what?' FROM t WHERE a = ?;") == 1
