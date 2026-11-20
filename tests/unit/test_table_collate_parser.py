from litemigrate.table_collate_parser import TableCollateParser

def test_collate_parser():
    ddl = "CREATE TABLE t (name TEXT COLLATE NOCASE, code TEXT COLLATE RTRIM)"
    collations = TableCollateParser.parse_collations(ddl)
    assert collations == {"name": "NOCASE", "code": "RTRIM"}
