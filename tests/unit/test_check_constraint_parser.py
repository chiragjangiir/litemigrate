from litemigrate.check_constraint_parser import CheckConstraintParser

def test_extract_checks():
    sql = "CREATE TABLE products (id INT, price NUMERIC CHECK(price > 0), status TEXT CHECK(status IN ('a', 'b')))"
    checks = CheckConstraintParser.extract_checks(sql)
    assert len(checks) == 2
    assert checks[0] == "price > 0"
