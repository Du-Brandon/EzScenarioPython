from __future__ import annotations

import pytest

from ezspec.argument import Argument
from ezspec.environment import ScenarioEnvironment
from ezspec.table import Table


def test_create_environment_has_no_arguments() -> None:
    env = ScenarioEnvironment.create()

    assert not env.hasArgument()
    assert env.getArgs() == ()
    assert env.getExecutionCount() == 0


def test_context_values_are_shared_through_java_compatible_accessors() -> None:
    env = ScenarioEnvironment.create()

    assert env.put("price", "20,000") is env
    assert env.get("price", str) == "20,000"
    assert env.gets("price") == "20,000"
    assert env.geti("price") == 20_000
    assert env.gets("missing") == ""


def test_arguments_support_indexes_names_numbers_percentages_and_history() -> None:
    env = ScenarioEnvironment.create()
    env.setArguments(
        [
            Argument("$20,000"),
            Argument("${VAT=5%}"),
            Argument("${ratio:1.25}"),
        ]
    )

    assert env.hasArgument()
    assert env.getArg(0) == "20,000"
    assert env.getArg("VAT") == "5%"
    assert env.getArgi(0) == 20_000
    assert env.getArgd("VAT") == 0.05
    assert env.getArgd("ratio") == 1.25

    env.setArguments([Argument("$next")])
    assert env.getArg(0) == "next"
    assert env.getHistoricalArg(0) == "20,000"
    assert env.getHistoricalArg("VAT") == "5%"


def test_missing_named_argument_raises_a_clear_error() -> None:
    env = ScenarioEnvironment.create()

    with pytest.raises(LookupError, match="Argument not found"):
        env.getArg("unknown")


def test_anonymous_table_accessors_return_rows() -> None:
    env = ScenarioEnvironment.create()
    table = Table(
        """
        | owner | points |
        | Jill  | 100    |
        | Joe   | 50     |
        """
    )

    env.setAnonymousTable(table)

    assert env.table() is table
    assert env.row(0).get("owner") == "Jill"
    assert env.row("Joe").get("points") == "50"
    assert env.lastRow().get("owner") == "Joe"


def test_table_accessor_without_a_step_table_fails() -> None:
    with pytest.raises(RuntimeError, match="No anonymous table"):
        ScenarioEnvironment.create().table()


def test_clone_copies_user_context_and_history_but_not_current_arguments() -> None:
    original = ScenarioEnvironment.create()
    input_table = Table("| value |\n| 1 |")
    original.setInput(input_table)
    original.put("shared", {"answer": 42})
    original.setArguments([Argument("${number=10}")])

    cloned = ScenarioEnvironment.clone(original)

    assert cloned.getInput() is input_table
    assert cloned.get("shared") is original.get("shared")
    assert cloned.getArgs() == ()
    assert cloned.getHistoricalArg("number") == "10"
