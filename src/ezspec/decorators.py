"""Compatibility imports for the original flat decorator module."""

from .extension.pytest.decorators import (
    EzDynamicScenario,
    EzDynamicScenarioOutline,
    EzFeature,
    EzRule,
    EzScenario,
    EzScenarioOutline,
)
from .runtime_context import current_rule

__all__ = [
    "EzDynamicScenario",
    "EzDynamicScenarioOutline",
    "EzFeature",
    "EzRule",
    "EzScenario",
    "EzScenarioOutline",
    "current_rule",
]
