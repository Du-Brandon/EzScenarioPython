"""Fluent Gherkin step registration shared by executable and declarative models.

Extracted from the Python adaptation of ezSpec's RuntimeScenario.java.
Original Java author: Teddy Chen. Modified into a shared Python mixin;
see NOTICE and docs/SOURCE_PROVENANCE.md.
"""

from __future__ import annotations

from typing import Any, Self

from .step import (
    And,
    But,
    Given,
    Step,
    StepCallback,
    Then,
    ThenFailure,
    ThenSuccess,
    When,
)


class StepRegistrationMixin:
    """Append fresh step objects while preserving the existing DSL signatures."""

    _steps: list[Step]

    @staticmethod
    def _callback_args(
        continuous_or_callback: bool | StepCallback,
        callback: StepCallback | None,
    ) -> tuple[bool, StepCallback]:
        if callback is None and callable(continuous_or_callback):
            return Step.TerminateAfterFailure, continuous_or_callback
        if callback is None or not callable(callback):
            raise TypeError("callback must be callable")
        return bool(continuous_or_callback), callback

    def _append(
        self,
        step_type: type[Step],
        description: str,
        continuous_or_callback: bool | StepCallback,
        callback: StepCallback | None = None,
    ) -> Self:
        continuous, resolved_callback = self._callback_args(
            continuous_or_callback, callback
        )
        self._steps.append(step_type(description, continuous, resolved_callback))
        return self

    def Given(self, description: str, continuous_or_callback: bool | StepCallback,
              callback: StepCallback | None = None) -> Self:
        return self._append(Given, description, continuous_or_callback, callback)

    given = Given

    def When(self, description: str, continuous_or_callback: bool | StepCallback,
             callback: StepCallback | None = None) -> Self:
        return self._append(When, description, continuous_or_callback, callback)

    when = When

    def Then(self, description: str, continuous_or_callback: bool | StepCallback,
             callback: StepCallback | None = None) -> Self:
        return self._append(Then, description, continuous_or_callback, callback)

    then = Then

    def And(self, description: str, continuous_or_callback: bool | StepCallback,
            callback: StepCallback | None = None) -> Self:
        return self._append(And, description, continuous_or_callback, callback)

    and_ = And

    def But(self, description: str, continuous_or_callback: bool | StepCallback,
            callback: StepCallback | None = None) -> Self:
        return self._append(But, description, continuous_or_callback, callback)

    but = But

    @staticmethod
    def _then_special_args(args: tuple[Any, ...]) -> tuple[str, bool, StepCallback]:
        description = ""
        continuous = Step.TerminateAfterFailure
        callback: StepCallback | None = None

        if len(args) == 1 and callable(args[0]):
            callback = args[0]
        elif len(args) == 2 and isinstance(args[0], bool) and callable(args[1]):
            continuous, callback = args
        elif len(args) == 2 and isinstance(args[0], str) and callable(args[1]):
            description, callback = args
        elif (
            len(args) == 3
            and isinstance(args[0], str)
            and isinstance(args[1], bool)
            and callable(args[2])
        ):
            description, continuous, callback = args
        else:
            raise TypeError(
                "expected callback, bool/callback, description/callback, "
                "or description/bool/callback"
            )
        return description, continuous, callback

    def ThenSuccess(self, *args: Any) -> Self:
        description, continuous, callback = self._then_special_args(args)
        return self._append(ThenSuccess, description, continuous, callback)

    then_success = ThenSuccess

    def ThenFailure(self, *args: Any) -> Self:
        description, continuous, callback = self._then_special_args(args)
        return self._append(ThenFailure, description, continuous, callback)

    then_failure = ThenFailure
