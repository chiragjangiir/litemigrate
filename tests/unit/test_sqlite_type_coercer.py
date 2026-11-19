from litemigrate.sqlite_type_coercer import SqliteTypeCoercer

def test_type_coercer():
    assert SqliteTypeCoercer.coerce_for_storage(True) == 1
    assert SqliteTypeCoercer.coerce_for_storage(False) == 0
    assert SqliteTypeCoercer.coerce_for_storage(123) == 123
    assert SqliteTypeCoercer.coerce_for_storage({"a": 1}) == "{'a': 1}"
