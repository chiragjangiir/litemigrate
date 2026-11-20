from litemigrate.partial_index_predicate_validator import PartialIndexPredicateValidator

def test_partial_index_validator():
    assert PartialIndexPredicateValidator.is_valid_where_clause("deleted_at IS NULL") is True
    assert PartialIndexPredicateValidator.is_valid_where_clause("id > 0 AND (status = 'active')") is True
    assert PartialIndexPredicateValidator.is_valid_where_clause("id > 0; DROP TABLE") is False
