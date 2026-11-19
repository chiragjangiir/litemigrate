class SqliteBackupProgressTracker:
    def __init__(self):
        self.remaining_pages = -1
        self.total_pages = -1

    def progress_callback(self, status: int, remaining: int, total: int):
        self.remaining_pages = remaining
        self.total_pages = total

    @property
    def percentage(self) -> float:
        if self.total_pages <= 0:
            return 0.0
        copied = self.total_pages - self.remaining_pages
        return round((copied / self.total_pages) * 100.0, 2)
