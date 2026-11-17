from litemigrate.pragma_compiler import get_recommended_pragmas

def test_recommended_pragmas():
    pragmas = get_recommended_pragmas()
    assert len(pragmas) == 5
    assert "PRAGMA journal_mode = WAL;" in pragmas
