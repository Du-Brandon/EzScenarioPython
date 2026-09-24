"""Step-description arguments.

Adapted from ezSpec's Argument.java. Original Java author: Teddy Chen.
Modified for Python; see NOTICE and docs/SOURCE_PROVENANCE.md.
"""

from __future__ import annotations

import re
from typing import Final, overload


_UNSET: Final = object()


class Argument:
    """A value argument (``$value``) or key/value argument (``${key:value}``)."""

    def __init__(self, expression: str | None = None) -> None:
        self._key: str | None = None
        self._value: str | None = None
        if expression is not None:
            self._parse(expression)

    @classmethod
    def create(cls, expression: str) -> Argument:
        """Create an argument from its textual expression."""

        return cls(expression)

    @classmethod
    def fromKey(cls, key: str) -> Argument:
        """Create an argument that currently contains only a key."""

        argument = cls()
        argument.key(key)
        return argument

    from_key = fromKey

    @staticmethod
    def _is_key_value(expression: str) -> bool:
        stripped = expression.strip()
        return stripped.startswith("${") and stripped.endswith("}")

    def _parse(self, expression: str) -> None:
        stripped = expression.strip()
        if self._is_key_value(stripped):
            match = re.fullmatch(r"\$\{([^=:]+)[=:](.+)\}", stripped)
            if match is not None:
                self._key = match.group(1).strip()
                self._value = match.group(2).strip()
            return

        match = re.search(r"\$\S+", expression)
        if match is not None:
            self._key = ""
            self._value = match.group(0)[1:].strip()

    @overload
    def key(self) -> str | None: ...

    @overload
    def key(self, new_key: str) -> None: ...

    def key(self, new_key: str | object = _UNSET) -> str | None:
        """Get or set the argument key, matching the overloaded Java API."""

        if new_key is _UNSET:
            return self._key
        if not isinstance(new_key, str):
            raise TypeError("key must be a string")
        self._key = new_key
        return None

    @overload
    def value(self) -> str | None: ...

    @overload
    def value(self, new_value: str) -> None: ...

    def value(self, new_value: str | object = _UNSET) -> str | None:
        """Get or set the argument value, matching the overloaded Java API."""

        if new_value is _UNSET:
            return self._value
        if not isinstance(new_value, str):
            raise TypeError("value must be a string")
        self._value = new_value
        return None
