import unittest
from litemigrate.cli import create_parser

class TestCliQuiet(unittest.TestCase):
    def test_quiet_flag_parsed(self):
        parser = create_parser()
        args = parser.parse_args(["--quiet", "inspect", "--db", "app.db"])
        self.assertTrue(args.quiet)
