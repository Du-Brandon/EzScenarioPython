"""Collection hooks that let ezSpec decorators participate in pytest."""

from __future__ import annotations

import inspect
from typing import Any

import pytest

from . import reporting as report_lifecycle
from .collection import CASE_FIXTURE, generate_cases, get_catalog, prepare_function
from .compat import collect_functions
from .decorators import get_outline_config
from .execution import execute_item
from .registry import get_registry


_EXECUTED_ITEMS = pytest.StashKey[dict[str, pytest.Item]]()


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
        outline = get_outline_config(obj)
        if outline is not None:
            prepare_function(obj)
        items = collect_functions(collector, name, obj)
        if outline is not None:
            catalog = get_catalog(collector.config, obj)
            registry = get_registry(collector.config)
            for item in items:
                registry.register_item(item, catalog, item.callspec.params[CASE_FIXTURE])
        return items
    return None


def pytest_addoption(parser: pytest.Parser) -> None:
    """Register ezSpec report command-line options."""

    report_lifecycle.pytest_addoption(parser)
    parser.getgroup("ezspec report").addoption(
        "--ezspec-steps", action="store_true", default=False,
        help="show Gherkin step results for executed outline rows",
    )


@pytest.fixture
def _ezspec_case(request: pytest.FixtureRequest):
    return request.param


@pytest.hookimpl(trylast=True)
def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    generate_cases(metafunc)


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_collection_modifyitems(
    config: pytest.Config,
    items: list[pytest.Item],
):
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

    report_items = list(items)
    yield
    get_registry(config).mark_selected(items)
    report_lifecycle.pytest_collection_modifyitems(config, report_items)


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item: pytest.Item) -> None:
    if get_outline_config(getattr(item, "obj", None)) is not None:
        get_registry(item.config).begin_attempt(item)
        item.config.stash.setdefault(_EXECUTED_ITEMS, {})[item.nodeid] = item


@pytest.hookimpl(tryfirst=True)
def pytest_pyfunc_call(pyfuncitem: pytest.Function) -> bool | None:
    return execute_item(pyfuncitem)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo):
    outcome = yield
    report = outcome.get_result()
    if get_outline_config(getattr(item, "obj", None)) is not None:
        registry = get_registry(item.config)
        registry.record_phase(item, report)
        if report.failed:
            details = registry.format_item_steps(item)
            if details:
                report.sections.append(("ezSpec steps", details))


def pytest_terminal_summary(terminalreporter, exitstatus: int, config: pytest.Config):
    if config.getoption("ezspec_steps"):
        registry = get_registry(config)
        for item in config.stash.get(_EXECUTED_ITEMS, {}).values():
            details = registry.format_item_steps(item)
            if details:
                terminalreporter.write_sep("-", item.nodeid)
                terminalreporter.write_line(details)


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """Generate requested living-documentation reports."""

    report_lifecycle.pytest_sessionfinish(session, exitstatus)
