"""Gherkin step model and keyword-specific step classes.

Adapted from ezSpec's Step.java, step keyword classes, and ConcurrentGroup.java.
Original Java author: Teddy Chen. Modified for Python;
see NOTICE and docs/SOURCE_PROVENANCE.md.
"""

from __future__ import annotations

import re
from collections.abc import Callable

from .argument import Argument
from .environment import ScenarioEnvironment
from .result import Result

StepCallback = Callable[[ScenarioEnvironment], None]


class Step:
    ContinuousAfterFailure = True
    TerminateAfterFailure = False

    KEYWORD = "Step"

    def __init__(
        self,
        description: str,
        continuous: bool = TerminateAfterFailure,
        callback: StepCallback | None = None,
    ) -> None:
        if callback is None and callable(continuous):
            callback = continuous
            continuous = self.TerminateAfterFailure
        if callback is None or not callable(callback):
            raise TypeError("callback must be callable")
        if not isinstance(description, str):
            raise TypeError("description must be a string")

        if description.endswith("\n"):
            description = description[:-1]
        self._description = description.strip()
        self._continuous_after_failure = bool(continuous)
        self._callback = callback
        self._result = Result.Pending(None)

    def isContinuousAfterFailure(self) -> bool:
        return self._continuous_after_failure

    is_continuous_after_failure = isContinuousAfterFailure

    def getCallback(self) -> StepCallback:
        return self._callback

    get_callback = getCallback

    def description(self) -> str:
        return self._description

    def getResult(self) -> Result:
        return self._result

    get_result = getResult

    def setResult(self, result: Result) -> None:
        self._result = result

    set_result = setResult

    def getName(self) -> str:
        return self.KEYWORD

    get_name = getName

    def accept(self, visitor: object) -> None:
        """Dispatch this step to a specification visitor."""

        visit = getattr(visitor, "visit")
        visit(self)

    @staticmethod
    def parseArguments(description: str) -> list[Argument]:
        # Prefixing one blank lets an argument at the start use the same rule as
        # arguments following normal words, exactly as in the Java version.
        pattern = re.compile(r"\s\$\{[^}]+\}|\s\$[^\s^{]+")
        return [Argument(match.group(0)) for match in pattern.finditer(" " + description)]

    parse_arguments = parseArguments

    @staticmethod
    def eraseTable(description: str) -> str:
        return "".join(
            line
            for line in description.splitlines()
            if not line.startswith(("|", "<|", ">"))
        )

    erase_table = eraseTable

    @staticmethod
    def eraseReservedWords(description: str) -> str:
        # Named values must be expanded before anonymous values, otherwise the
        # dollar sign opening ${...} would be consumed by the second pattern.
        description = re.sub(
            r"\s\$\{[^}]+\}",
            lambda match: " "
            + re.split(r"[=:]", match.group(0).strip()[2:-1], maxsplit=1)[1],
            description,
        )
        description = re.sub(
            r"(?<!\S)\$(?!\{)(\S+)",
            lambda match: match.group(1),
            description,
        )
        return description.strip()

    erase_reserved_words = eraseReservedWords


class ConcurrentGroup:
    """Marker mixin for the first step in a concurrent group."""


class Given(Step, ConcurrentGroup):
    KEYWORD = "Given"


class When(Step, ConcurrentGroup):
    KEYWORD = "When"


class Then(Step, ConcurrentGroup):
    KEYWORD = "Then"


class ThenSuccess(Step, ConcurrentGroup):
    KEYWORD = "Then success"


class ThenFailure(Step, ConcurrentGroup):
    KEYWORD = "Then failure"


class And(Step):
    KEYWORD = "And"


class But(Step):
    KEYWORD = "But"


CONCURRENT_GROUP_STARTS = (Given, When, Then, ThenSuccess, ThenFailure)


ContinuousAfterFailure = Step.ContinuousAfterFailure
TerminateAfterFailure = Step.TerminateAfterFailure
