import unittest
from litemigrate.bench_harness import run_profiled_execution

class TestBenchHarness(unittest.TestCase):
    def test_measures_execution_times(self):
        res = run_profiled_execution("noop", lambda: None, iterations=5)
        self.assertEqual(res["benchmark"], "noop")
        self.assertEqual(res["iterations"], 5)
        self.assertGreaterEqual(res["mean_ms"], 0.0)
