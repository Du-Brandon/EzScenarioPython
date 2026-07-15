import pytest

from ezspec.result import Result, StepExecutionOutcome


@pytest.mark.parametrize(
    ("result", "outcome", "predicate"),
    [
        (Result.Success(), StepExecutionOutcome.Success, "isSuccess"),
        (Result.Failure(RuntimeError()), StepExecutionOutcome.Failure, "isFailure"),
        (Result.Skip(), StepExecutionOutcome.Skipped, "isSkipped"),
        (Result.Pending(RuntimeError()), StepExecutionOutcome.Pending, "isPending"),
    ],
)
def test_result_has_exactly_one_execution_outcome(
    result: Result,
    outcome: StepExecutionOutcome,
    predicate: str,
) -> None:
    assert result.getExecutionOutcome() is outcome
    assert str(result) == outcome.value
    assert getattr(result, predicate)()
    assert sum(
        (
            result.isSuccess(),
            result.isFailure(),
            result.isSkipped(),
            result.isPending(),
        )
    ) == 1


def test_failure_requires_an_exception() -> None:
    with pytest.raises(TypeError, match="must not be None"):
        Result.Failure(None)  # type: ignore[arg-type]


def test_failure_and_pending_messages() -> None:
    failure = Result.Failure(AssertionError("expected: 1 but was 2"))
    pending = Result.Pending(RuntimeError("waiting for service"))

    assert failure.getFailureMessage() == "[anticipated: 1 but was 2]"
    assert pending.getFailureMessage() == "[waiting for service]"
    assert Result.Success().getFailureMessage() == ""
    assert Result.Skip().getFailureMessage() == ""


def test_stack_trace_is_available_for_a_raised_exception() -> None:
    captured: RuntimeError
    try:
        raise RuntimeError("boom")
    except RuntimeError as error:
        captured = error
        result = Result.Failure(error)

    assert "test_stack_trace_is_available_for_a_raised_exception" in result.getStackTrace()
    assert "test_result.py" in result.getFailureMessage()
    assert result.getException() is captured
