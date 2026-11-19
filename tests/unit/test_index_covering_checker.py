from litemigrate.index_covering_checker import IndexCoveringChecker

def test_is_covering():
    assert IndexCoveringChecker.is_covering(["id", "username", "email"], ["id", "email"]) is True
    assert IndexCoveringChecker.is_covering(["id", "username"], ["id", "email"]) is False
