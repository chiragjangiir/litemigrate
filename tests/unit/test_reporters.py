import unittest
from litemigrate.reporters import render_markdown_summary


class TestReporters(unittest.TestCase):
    def test_render_passed_summary(self):
        md = render_markdown_summary("passed", 12.34, 0, True, 5)
        self.assertIn("✅ LiteMigrate Shadow Validation Summary", md)
        self.assertIn("| **Verdict** | `PASSED` |", md)
        self.assertIn("| **Foreign Key Violations** | 0 |", md)
        self.assertIn("| **Database Integrity** | `PASSED` |", md)

    def test_render_failed_summary(self):
        md = render_markdown_summary("failed", 45.67, 3, False, 2)
        self.assertIn("❌ LiteMigrate Shadow Validation Summary", md)
        self.assertIn("| **Foreign Key Violations** | 3 |", md)
        self.assertIn("| **Database Integrity** | `FAILED` |", md)


if __name__ == "__main__":
    unittest.main()
