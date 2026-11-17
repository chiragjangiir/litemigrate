import sqlite3
from litemigrate.json_validator import is_json_valid_supported

def test_json_valid_supported():
    conn = sqlite3.connect(":memory:")
    assert is_json_valid_supported(conn) is True
