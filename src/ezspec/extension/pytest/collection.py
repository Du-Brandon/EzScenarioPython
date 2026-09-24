"""Normalize declared Examples and expand them through pytest parametrization."""

from __future__ import annotations

import inspect
from typing import Any

import pytest

from ...keyword.case import ExampleCatalog, normalize_examples
from .decorators import get_outline_config


CASE_FIXTURE = "_ezspec_case"
_CATALOGS = pytest.StashKey[dict[Any, ExampleCatalog]]()


def prepare_function(function: Any) -> None:
    """Request the internal case fixture without changing the user signature."""

    if CASE_FIXTURE in inspect.signature(function).parameters:
        raise pytest.UsageError(f"{CASE_FIXTURE} is reserved for ezSpec")
    if not getattr(function, "__ezspec_case_fixture__", False):
        pytest.mark.usefixtures(CASE_FIXTURE)(function)
        function.__ezspec_case_fixture__ = True


def get_catalog(config: pytest.Config, function: Any) -> ExampleCatalog:
    catalogs = config.stash.setdefault(_CATALOGS, {})
    if function not in catalogs:
        declaration = get_outline_config(function)
        if declaration is None:
            raise ValueError("the function does not declare outline examples")
        try:
            catalogs[function] = normalize_examples(declaration.examples)
        except (TypeError, ValueError, RuntimeError) as error:
            raise pytest.UsageError(
                f"{function.__module__}.{function.__qualname__}: invalid Examples: {error}"
            ) from error
    return catalogs[function]


def generate_cases(metafunc: pytest.Metafunc) -> None:
    if get_outline_config(metafunc.function) is None:
        return
    for marker in metafunc.definition.iter_markers("parametrize"):
        names = marker.args[0] if marker.args else marker.kwargs.get("argnames", ())
        names = names.split(",") if isinstance(names, str) else names
        if CASE_FIXTURE in (name.strip() for name in names):
            raise pytest.UsageError(f"{CASE_FIXTURE} is reserved for ezSpec")
    catalog = get_catalog(metafunc.config, metafunc.function)
    # A placeholder preserves Java's zero-callback, successful no-op semantics
    # independently of pytest's configurable empty_parameter_set_mark.
    cases = catalog.cases or (None,)
    metafunc.parametrize(
        CASE_FIXTURE,
        cases,
        indirect=True,
        ids=[case.id if case is not None else "no-examples" for case in cases],
    )
