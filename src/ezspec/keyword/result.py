"""Execution outcomes and step results."""

from __future__ import annotations

import traceback
from enum import Enum


class StepExecutionOutcome(Enum):
    """The possible execution states of a step."""

    Pending = "Pending"
    Success = "Success"
    Failure = "Failure"
    Skipped = "Skipped"

    # Conventional Python enum aliases without breaking the Java names.
    PENDING = Pending
    SUCCESS = Success
    FAILURE = Failure
    SKIPPED = Skipped

    def __str__(self) -> str:
        return self.value


class Result:
    """The outcome of executing one scenario step."""

    def __init__(
        self,
        outcome: StepExecutionOutcome,
        error: BaseException | None = None,
    ) -> None:
        self._execution_outcome = outcome
        self._error = error

    @classmethod
    def Success(cls) -> Result:
        return cls(StepExecutionOutcome.Success)

    @classmethod
    def Failure(cls, error: BaseException) -> Result:
        if error is None:
            raise TypeError("error must not be None")
        return cls(StepExecutionOutcome.Failure, error)

    @classmethod
    def Skip(cls) -> Result:
        return cls(StepExecutionOutcome.Skipped)

    @classmethod
    def Pending(cls, error: BaseException | None = None) -> Result:
        return cls(StepExecutionOutcome.Pending, error)

    # Pythonic factory aliases.
    success = Success
    failure = Failure
    skip = Skip
    pending = Pending

    def getStackTrace(self) -> str:
        if self._error is None or self._error.__traceback__ is None:
            return ""
        frames = traceback.extract_tb(self._error.__traceback__)
        return "\n".join(frame.strip() for frame in traceback.format_list(frames))

    get_stack_trace = getStackTrace

    def getExecutionOutcome(self) -> StepExecutionOutcome:
        return self._execution_outcome

    get_execution_outcome = getExecutionOutcome

    def isSuccess(self) -> bool:
        return self._execution_outcome is StepExecutionOutcome.Success

    is_success = isSuccess

    def isFailure(self) -> bool:
        return self._execution_outcome is StepExecutionOutcome.Failure

    is_failure = isFailure

    def isSkipped(self) -> bool:
        return self._execution_outcome is StepExecutionOutcome.Skipped

    is_skipped = isSkipped

    def isPending(self) -> bool:
        return self._execution_outcome is StepExecutionOutcome.Pending

    is_pending = isPending

    def getException(self) -> BaseException | None:
        return self._error

    get_exception = getException

    def getFailureMessage(self) -> str:
        if self._execution_outcome is StepExecutionOutcome.Failure:
            location = self._failure_location()
            message = self._exception_message()
            return f"{location}[{message}]"
        if self._execution_outcome is StepExecutionOutcome.Pending:
            message = self._exception_message()
            return f"[{message}]" if message else ""
        return ""

    get_failure_message = getFailureMessage

    def _failure_location(self) -> str:
        if self._error is None or self._error.__traceback__ is None:
            return ""
        frame = traceback.extract_tb(self._error.__traceback__)[-1]
        return f'{frame.filename}:{frame.lineno} in {frame.name}'

    def _exception_message(self) -> str:
        if self._error is None:
            return ""
        return str(self._error).replace("expected: ", "anticipated: ")

    def __str__(self) -> str:
        return str(self._execution_outcome)
