"""Collection hooks that let ezSpec decorators participate in pytest."""

from __future__ import annotations

import inspect
from typing import Any

import pytest

from . import reporting as report_lifecycle


_SCENARIO_KINDS = {
    "scenario",
    "scenario_outline",
    "dynamic_scenario",
    "dynamic_scenario_outline",
}


def pytest_pycollect_makeitem(
    collector: pytest.Collector,
    name: str,
    obj: Any,
) -> pytest.Collector | list[pytest.Collector] | None:
    """Collect decorated classes and methods regardless of pytest naming."""

    kind = getattr(obj, "__ezspec_kind__", None)
    kinds = getattr(obj, "__ezspec_kinds__", ())
    if inspect.isclass(obj) and ({"feature", "rule"} & set(kinds)):
        return pytest.Class.from_parent(collector, name=name, obj=obj)
    if callable(obj) and kind in _SCENARIO_KINDS:
        if isinstance(collector, pytest.Class):
            return pytest.Function.from_parent(collector, name=name)
        return pytest.Function.from_parent(collector, name=name, callobj=obj)
    return None


def pytest_addoption(parser: pytest.Parser) -> None:
    """Register ezSpec report command-line options."""

    report_lifecycle.pytest_addoption(parser)


def pytest_collection_modifyitems(
    config: pytest.Config,
    items: list[pytest.Item],
) -> None:
    """Attach readable markers for filtering and reporting."""

    for item in items:
        obj = getattr(item, "obj", None)
        kind = getattr(obj, "__ezspec_kind__", None)
        owner = getattr(item, "cls", None)
        owner_kinds = getattr(owner, "__ezspec_kinds__", ())
        if "feature" in owner_kinds:
            item.add_marker(pytest.mark.ezfeature)
        if kind in {"scenario", "dynamic_scenario"}:
            item.add_marker(pytest.mark.ezscenario)
        elif kind in {"scenario_outline", "dynamic_scenario_outline"}:
            item.add_marker(pytest.mark.ezscenario_outline)

    report_lifecycle.pytest_collection_modifyitems(config, items)


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """Generate requested living-documentation reports."""

    report_lifecycle.pytest_sessionfinish(session, exitstatus)
