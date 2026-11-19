from litemigrate.sqlite_backup_progress_tracker import SqliteBackupProgressTracker

def test_progress_tracker():
    tracker = SqliteBackupProgressTracker()
    tracker.progress_callback(0, 25, 100)
    assert tracker.percentage == 75.0
