from litemigrate.transaction_depth_tracker import TransactionTracker

def test_transaction_tracker():
    t = TransactionTracker()
    assert t.depth == 0
    sp1 = t.begin()
    assert sp1 == "sp_1"
    assert t.depth == 1
    t.commit()
    assert t.depth == 0
