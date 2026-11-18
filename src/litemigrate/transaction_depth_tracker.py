class TransactionTracker:
    def __init__(self):
        self.depth = 0

    def begin(self):
        self.depth += 1
        return f"sp_{self.depth}"

    def commit(self):
        if self.depth > 0:
            self.depth -= 1

    def rollback(self):
        if self.depth > 0:
            self.depth -= 1
