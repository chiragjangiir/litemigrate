import unittest
from litemigrate.retry import retry_with_backoff

class TestRetry(unittest.TestCase):
    def test_succeeds_on_transient_failure(self):
        attempts = 0
        def flappy():
            nonlocal attempts
            attempts += 1
            if attempts < 3:
                raise ValueError("temporary error")
            return "success"

        res = retry_with_backoff(flappy, max_attempts=5, initial_delay=0.001)
        self.assertEqual(res, "success")
        self.assertEqual(attempts, 3)
