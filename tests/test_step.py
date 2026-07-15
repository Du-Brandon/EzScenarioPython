from __future__ import annotations

from ezspec.result import StepExecutionOutcome
from ezspec.step import And, But, Given, Step, Then, ThenFailure, ThenSuccess, When


def _noop(_env) -> None:
    pass


def test_step_trims_description_and_starts_pending() -> None:
    step = Given("  a condition\n", _noop)

    assert step.description() == "a condition"
    assert step.getName() == "Given"
    assert step.getCallback() is _noop
    assert not step.isContinuousAfterFailure()
    assert step.getResult().getExecutionOutcome() is StepExecutionOutcome.Pending


def test_all_keyword_names_match_java_api() -> None:
    assert [
        keyword("", _noop).getName()
        for keyword in (Given, When, Then, ThenSuccess, ThenFailure, And, But)
    ] == ["Given", "When", "Then", "Then success", "Then failure", "And", "But"]


def test_parse_arguments_finds_anonymous_and_named_values_in_order() -> None:
    arguments = Step.parseArguments(
        "pay ${total_price:21,000}, receive $$1,000 and ${gift=$$$keyboard}"
    )

    assert [argument.key() for argument in arguments] == [
        "total_price",
        "",
        "gift",
    ]
    assert [argument.value() for argument in arguments] == [
        "21,000",
        "$1,000",
        "$$$keyboard",
    ]


def test_dollar_followed_by_whitespace_is_not_an_argument() -> None:
    assert Step.parseArguments("price is $ 100") == []


def test_erase_reserved_words_preserves_values_for_readable_gherkin() -> None:
    text = "pay ${total:21,000} and receive $$1,000"

    assert Step.eraseReservedWords(text) == "pay 21,000 and receive $1,000"


def test_erase_table_removes_table_lines() -> None:
    description = "customers\n| name |\n| Jill |"

    assert Step.eraseTable(description) == "customers"
