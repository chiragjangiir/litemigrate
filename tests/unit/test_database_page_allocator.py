import sqlite3
from litemigrate.database_page_allocator import DatabasePageAllocator

def test_allocation_stats():
    conn = sqlite3.connect(":memory:")
    stats = DatabasePageAllocator.get_allocation_stats(conn)
    assert stats["page_size"] > 0
    assert "total_bytes" in stats
