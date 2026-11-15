"""Lifecycle hooks registry for migration phases."""
from __future__ import annotations
from typing import Callable, Any

HookFn = Callable[[str, dict[str, Any]], None]

class MigrationHookRegistry:
    def __init__(self) -> None:
        self._pre_hooks: list[HookFn] = []
        self._post_hooks: list[HookFn] = []

    def register_pre_hook(self, fn: HookFn) -> None:
        self._pre_hooks.append(fn)

    def register_post_hook(self, fn: HookFn) -> None:
        self._post_hooks.append(fn)

    def trigger_pre(self, phase: str, context: dict[str, Any]) -> None:
        for hook in self._pre_hooks:
            hook(phase, context)

    def trigger_post(self, phase: str, context: dict[str, Any]) -> None:
        for hook in self._post_hooks:
            hook(phase, context)
