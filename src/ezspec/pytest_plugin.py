"""Compatibility imports for the original pytest plugin module."""

from .extension.pytest.plugin import (
    _ezspec_case,
    pytest_addoption,
    pytest_collection_modifyitems,
    pytest_generate_tests,
    pytest_pyfunc_call,
    pytest_pycollect_makeitem,
    pytest_runtest_makereport,
    pytest_runtest_setup,
    pytest_sessionfinish,
    pytest_terminal_summary,
)

__all__ = [
    "pytest_addoption",
    "pytest_collection_modifyitems",
    "pytest_generate_tests",
    "pytest_pyfunc_call",
    "pytest_pycollect_makeitem",
    "pytest_runtest_makereport",
    "pytest_runtest_setup",
    "pytest_sessionfinish",
    "pytest_terminal_summary",
]
