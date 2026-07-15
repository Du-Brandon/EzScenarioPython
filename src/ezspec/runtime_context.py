"""Framework-neutral execution context shared by decorators and the domain."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar


_CURRENT_RULE: ContextVar[str] = ContextVar("ezspec_current_rule", default="")


def current_rule() -> str:
    """Return the rule selected for the currently executing specification."""

    return _CURRENT_RULE.get()


@contextmanager
def rule_scope(rule: str) -> Iterator[None]:
    """Select a rule for nested scenario construction and restore it afterward."""

    token = _CURRENT_RULE.set(rule)
    try:
        yield
    finally:
        _CURRENT_RULE.reset(token)
