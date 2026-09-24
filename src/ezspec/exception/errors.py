"""Exceptions used by the ezSpec execution model.

Adapted from ezSpec's EzSpecError.java and PendingException.java.
Original Java author: Teddy Chen. Modified for Python;
see NOTICE and docs/SOURCE_PROVENANCE.md.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import NoReturn


class EzSpecError(RuntimeError):
    """Raised when one or more scenario steps fail."""

    def __init__(
        self,
        source: str | BaseException | Sequence[BaseException],
        message: str | None = None,
    ) -> None:
        if isinstance(source, str):
            errors: tuple[BaseException, ...] = ()
            detail = source if message is None else message
        elif isinstance(source, BaseException):
            errors = (source,)
            detail = str(source) if message is None else message
        else:
            errors = tuple(source)
            detail = "" if message is None else message

        self.errors = errors
        super().__init__(detail)

        if len(errors) == 1:
            self.__cause__ = errors[0]


class PendingException(RuntimeError):
    """Signals that a step is specified but has not been implemented."""

    @staticmethod
    def pending(message: str | None = None) -> NoReturn:
        """Raise a pending-step exception, optionally with an explanation."""

        raise PendingException(message) if message is not None else PendingException()
