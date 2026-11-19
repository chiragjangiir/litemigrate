from litemigrate.column_default_evaluator import ColumnDefaultEvaluator

def test_dynamic_default():
    assert ColumnDefaultEvaluator.is_dynamic_default("CURRENT_TIMESTAMP") is True
    assert ColumnDefaultEvaluator.is_dynamic_default("(datetime('now'))") is True
    assert ColumnDefaultEvaluator.is_dynamic_default("'active'") is False
    assert ColumnDefaultEvaluator.is_dynamic_default(None) is False
