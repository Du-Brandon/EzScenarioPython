"""The small boundary around pytest's Python collection internals.

Constructing Function directly bypasses fixture discovery and parametrization.
Keep the internal calls here so pytest-version compatibility is tested in one
place, rather than reimplementing its collection and fixture machinery.
"""

from __future__ import annotations

from typing import Any

import pytest


def collect_functions(
    collector: pytest.Collector, name: str, function: Any
) -> list[pytest.Function]:
    generate = getattr(collector, "_genfunctions", None)
    if generate is None:
        raise pytest.UsageError("ezSpec requires pytest's Python module/class collector")
    return list(generate(name, function))


def function_arguments(item: pytest.Function) -> dict[str, Any]:
    """Use exactly the arguments pytest resolved for the user's function."""

    return {name: item.funcargs[name] for name in item._fixtureinfo.argnames}
