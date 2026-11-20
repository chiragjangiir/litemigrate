from litemigrate.column_affinity_coercer import ColumnAffinityCoercer

def test_affinity_coercer():
    assert ColumnAffinityCoercer.determine_affinity("VARCHAR(255)") == "TEXT"
    assert ColumnAffinityCoercer.determine_affinity("BIGINT") == "INTEGER"
    assert ColumnAffinityCoercer.determine_affinity("FLOAT") == "REAL"
    assert ColumnAffinityCoercer.determine_affinity("") == "BLOB"
