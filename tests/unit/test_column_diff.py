from litemigrate.column_diff import compute_column_alteration_diff

def test_compute_column_alteration_diff():
    before = ["id", "title", "legacy_notes"]
    after = ["id", "title", "updated_notes", "created_at"]
    diff = compute_column_alteration_diff(before, after)
    assert diff["added"] == ["updated_notes", "created_at"]
    assert diff["removed"] == ["legacy_notes"]
    assert diff["retained"] == ["id", "title"]
