from litemigrate.type_affinity import determine_sqlite_affinity

def test_determine_sqlite_affinity():
    assert determine_sqlite_affinity("INTEGER") == "INTEGER"
    assert determine_sqlite_affinity("BIGINT") == "INTEGER"
    assert determine_sqlite_affinity("VARCHAR(255)") == "TEXT"
    assert determine_sqlite_affinity("TEXT") == "TEXT"
    assert determine_sqlite_affinity("BLOB") == "BLOB"
    assert determine_sqlite_affinity("FLOAT") == "REAL"
    assert determine_sqlite_affinity("DECIMAL(10,2)") == "NUMERIC"
    assert determine_sqlite_affinity("") == "BLOB"
