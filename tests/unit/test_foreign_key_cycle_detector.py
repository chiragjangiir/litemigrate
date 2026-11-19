from litemigrate.foreign_key_cycle_detector import ForeignKeyCycleDetector

def test_has_cycles():
    no_cycle = {"orders": ["users"], "users": []}
    assert ForeignKeyCycleDetector.has_cycles(no_cycle) is False
    with_cycle = {"a": ["b"], "b": ["c"], "c": ["a"]}
    assert ForeignKeyCycleDetector.has_cycles(with_cycle) is True
