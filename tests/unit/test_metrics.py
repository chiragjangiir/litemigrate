import time
import unittest
from litemigrate.metrics import ExecutionTimer, calculate_throughput_rows_per_sec


class TestMetrics(unittest.TestCase):
    def test_execution_timer(self):
        timer = ExecutionTimer().start()
        time.sleep(0.01)
        elapsed = timer.stop()
        self.assertGreaterEqual(elapsed, 5.0)

    def test_throughput_calculator(self):
        self.assertEqual(calculate_throughput_rows_per_sec(0, 100.0), 0.0)
        self.assertEqual(calculate_throughput_rows_per_sec(1000, 0.0), 0.0)
        self.assertAlmostEqual(calculate_throughput_rows_per_sec(1000, 500.0), 2000.0)


if __name__ == "__main__":
    unittest.main()
