import unittest
from litemigrate.hooks import MigrationHookRegistry

class TestHooks(unittest.TestCase):
    def test_triggers_registered_hooks(self):
        registry = MigrationHookRegistry()
        calls = []
        registry.register_pre_hook(lambda p, c: calls.append(f"pre-{p}"))
        registry.register_post_hook(lambda p, c: calls.append(f"post-{p}"))

        registry.trigger_pre("shadow", {})
        registry.trigger_post("shadow", {})
        self.assertEqual(calls, ["pre-shadow", "post-shadow"])
