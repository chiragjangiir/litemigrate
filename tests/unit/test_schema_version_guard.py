import sqlite3
import pytest
from litemigrate.schema_version_guard import SchemaVersionGuard

def test_schema_version_guard():
    conn = sqlite3.connect(":memory:")
    new_v = SchemaVersionGuard.verify_and_increment(conn, 0)
    assert new_v == 1
    with pytest.raises(ValueError):
        SchemaVersionGuard.verify_and_increment(conn, 0)
