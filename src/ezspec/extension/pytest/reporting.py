"""pytest lifecycle hooks for ezSpec report generation."""

from __future__ import annotations

from typing import Any

import pytest

from ...report.decorators import (
    ReportConfig,
    get_report_config,
    is_report_disabled,
)
from ...report.generator import generate_feature_report


_REPORT_CLASSES = pytest.StashKey[tuple[type[Any], ...]]()


def pytest_addoption(parser: pytest.Parser) -> None:
    """Register report-related command-line options."""

    group = parser.getgroup("ezspec report")
    group.addoption(
        "--ezspec-report",
        action="store_true",
        default=False,
        help="generate reports for every collected @EzFeature class",
    )
    group.addoption(
        "--ezspec-report-dir",
        action="store",
        default=None,
        metavar="PATH",
        help="override the output directory for generated ezSpec reports",
    )


def _is_feature_class(owner: type[Any]) -> bool:
    return "feature" in getattr(owner, "__ezspec_kinds__", ())


def pytest_collection_modifyitems(
    config: pytest.Config,
    items: list[pytest.Item],
) -> None:
    """Remember report-enabled feature classes on this pytest Config."""

    force_all = bool(config.getoption("ezspec_report"))
    classes: list[type[Any]] = []
    seen: set[type[Any]] = set()
    for item in items:
        owner = getattr(item, "cls", None)
        if not isinstance(owner, type) or owner in seen:
            continue
        seen.add(owner)
        if is_report_disabled(owner):
            continue
        if get_report_config(owner) is not None or (
            force_all and _is_feature_class(owner)
        ):
            classes.append(owner)
    config.stash[_REPORT_CLASSES] = tuple(classes)


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """Generate reports after all collected scenarios have executed."""

    del exitstatus
    config = session.config
    output_dir = config.getoption("ezspec_report_dir")
    for owner in config.stash.get(_REPORT_CLASSES, ()):
        report_config = get_report_config(owner) or ReportConfig()
        generate_feature_report(owner, report_config, output_dir=output_dir)


__all__ = [
    "pytest_addoption",
    "pytest_collection_modifyitems",
    "pytest_sessionfinish",
]
