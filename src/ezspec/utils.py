"""Compatibility imports for the original flat utility module."""

from .extension.utils import (
    SpecUtils,
    center,
    delete_end_with_new_line,
    get_replaced_underscores,
)

__all__ = [
    "SpecUtils",
    "center",
    "delete_end_with_new_line",
    "get_replaced_underscores",
]
