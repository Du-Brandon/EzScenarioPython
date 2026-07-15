"""Compatibility imports for the original pytest plugin module."""

from .extension.pytest.plugin import (
    pytest_addoption,
    pytest_collection_modifyitems,
    pytest_pycollect_makeitem,
    pytest_sessionfinish,
)

__all__ = [
    "pytest_addoption",
    "pytest_collection_modifyitems",
    "pytest_pycollect_makeitem",
    "pytest_sessionfinish",
]
