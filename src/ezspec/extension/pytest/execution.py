"""Execute only the selected Examples row after pytest has set up fixtures."""

from __future__ import annotations

import inspect

import pytest

from ...keyword.definition import OutlineDefinition
from .collection import CASE_FIXTURE
from .compat import function_arguments
from .decorators import get_outline_config
from .registry import get_registry


def execute_item(item: pytest.Function) -> bool | None:
    if get_outline_config(item.obj) is None:
        return None
    case = item.funcargs[CASE_FIXTURE]
    if case is None:
        return True
    if inspect.iscoroutinefunction(inspect.unwrap(item.obj)):
        raise TypeError(f"{item.nodeid}: async outline declarations are not supported")
    definition = item.obj(**function_arguments(item))
    if not isinstance(definition, OutlineDefinition):
        raise TypeError(
            f"{item.nodeid}: an outline with examples= must return an "
            "OutlineDefinition from feature.defineScenarioOutline(); "
            "do not call Execute() in the declaration"
        )
    registry = get_registry(item.config)
    registry.validate_definition(item, definition)
    runtime = definition.build_case(case)
    try:
        runtime.Execute()
    finally:
        registry.record_runtime(item, definition, runtime)
    return True
