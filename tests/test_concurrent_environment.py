from __future__ import annotations

from collections import Counter
from threading import Barrier, Event

import pytest

from ezspec.argument import Argument
from ezspec.environment import ScenarioEnvironment
from ezspec.exceptions import EzSpecError
from ezspec.keyword.rule import Background
from ezspec.scenario import RuntimeScenario
from ezspec.step import Step
from ezspec.table import Table


def test_concurrent_arguments_are_local_through_all_public_accessors() -> None:
    scenario = RuntimeScenario("independent arguments")
    entered = Barrier(3)

    def member(name: str, number: int, percent: int):
        def callback(env: ScenarioEnvironment) -> None:
            entered.wait(timeout=5)
            assert env is scenario.getEnvironment()
            assert env.hasArgument()
            assert [arg.value() for arg in env.getArgs()] == [
                name, f"{number:,}", f"{percent}%"
            ]
            assert env.getArg(0) == name
            assert env.getArg("member") == name
            assert env.getArgi(1) == number
            assert env.getArgi("amount") == number
            assert env.getArgd("rate") == percent / 100
            assert tuple(env.get(ScenarioEnvironment.ARGUMENTS_KEY)) == env.getArgs()
            assert scenario.getEnvironment().getArg("member") == name

        return callback

    def no_arguments(env: ScenarioEnvironment) -> None:
        entered.wait(timeout=5)
        assert not env.hasArgument()
        assert env.getArgs() == ()
        assert env.get(ScenarioEnvironment.ARGUMENTS_KEY) == []
        with pytest.raises(LookupError, match="Argument not found"):
            env.getArg("member")

    scenario.Given(
        "${member=left} ${amount=1,000} ${rate=5%}", member("left", 1000, 5)
    ).And(
        "${member=right} ${amount=2,000} ${rate=8%}", member("right", 2000, 8)
    ).But("without arguments", no_arguments).ExecuteConcurrently()


def test_concurrent_tables_and_active_table_are_local_to_their_step() -> None:
    input_table = Table("| input |\n| original |")
    scenario = RuntimeScenario("independent tables", table=input_table)
    entered = Barrier(3)

    def member(name: str):
        def callback(env: ScenarioEnvironment) -> None:
            entered.wait(timeout=5)
            assert env.row(0).get("member") == name
            assert env.row(name).get("value") == "first"
            assert env.lastRow().get("value") == "last"
            assert env.table() is env.get(ScenarioEnvironment.ANONYMOUS_TABLE_KEY)
            assert scenario.activeTable() is env.table()
            assert scenario.getEnvironment().table() is env.table()
            assert env.getInput() is input_table

        return callback

    def no_table(env: ScenarioEnvironment) -> None:
        entered.wait(timeout=5)
        assert env.get(ScenarioEnvironment.ANONYMOUS_TABLE_KEY) is None
        with pytest.raises(RuntimeError, match="No anonymous table"):
            env.table()
        assert scenario.activeTable() is input_table

    scenario.Given(
        "left table\n| member | value |\n| left | first |\n| end | last |",
        member("left"),
    ).And(
        "right table\n| member | value |\n| right | first |\n| end | last |",
        member("right"),
    ).But("no table", no_table).ExecuteConcurrently()


@pytest.mark.parametrize("from_background", [False, True], ids=["previous-group", "background"])
def test_tableless_step_inherits_only_the_table_before_its_group(
    from_background: bool,
) -> None:
    description = "baseline\n| member |\n| inherited |"
    if from_background:
        background = Background("shared background", None)
        background.Given(description, lambda env: None).Execute()
        scenario = RuntimeScenario("inherit background table", background=background)
    else:
        scenario = RuntimeScenario("inherit previous group table")
        scenario.Given(description, lambda env: None)

    entered = Barrier(3)

    def member(expected: str):
        def callback(env: ScenarioEnvironment) -> None:
            entered.wait(timeout=5)
            assert env.row(0).get("member") == expected
            assert scenario.activeTable().row(0).get("member") == expected

        return callback

    scenario.When("left\n| member |\n| left |", member("left")).And(
        "right\n| member |\n| right |", member("right")
    ).But("inherit without table", member("inherited")).ExecuteConcurrently()


def test_user_values_remain_shared_and_input_and_execution_count_are_unchanged() -> None:
    input_table = Table("| value |\n| source |")
    scenario = RuntimeScenario("shared user context", table=input_table)
    scenario.getEnvironment().setExecutionCount(7)
    published, received = Event(), Event()
    shared_object = {"state": "ready"}

    def producer(env: ScenarioEnvironment) -> None:
        env.put("shared object", shared_object)
        published.set()
        assert received.wait(timeout=5)
        assert env.get("acknowledged") is True
        assert env.getInput() is input_table
        assert env.getExecutionCount() == 7

    def consumer(env: ScenarioEnvironment) -> None:
        assert published.wait(timeout=5)
        try:
            assert env.get("shared object") is shared_object
            assert env.getInput() is input_table
            assert env.getExecutionCount() == 7
            env.put("acknowledged", True)
        finally:
            received.set()

    scenario.Given("producer", producer).And("consumer", consumer).ExecuteConcurrently()
    assert scenario.getEnvironment().get("shared object") is shared_object
    assert scenario.getEnvironment().get("acknowledged") is True


def test_public_argument_and_table_setters_only_change_the_current_callback() -> None:
    scenario = RuntimeScenario("callback updates")
    entered, updated = Barrier(2), Barrier(2)

    def member(name: str):
        def callback(env: ScenarioEnvironment) -> None:
            entered.wait(timeout=5)
            env.setArguments([Argument("${member=" + name + "}")])
            env.setAnonymousTable(Table(f"| member |\n| {name} |"))
            updated.wait(timeout=5)
            assert env.getArg("member") == name
            assert env.row(0).get("member") == name
            assert env.get(ScenarioEnvironment.ARGUMENTS_KEY)[0].value() == name
            assert env.get(ScenarioEnvironment.ANONYMOUS_TABLE_KEY) is env.table()

        return callback

    scenario.Given("${initial=first}", member("left")).And(
        "${initial=second}", member("right")
    ).ExecuteConcurrently()
    assert Counter(arg.value() for arg in scenario.getEnvironment().getHistoricalArgs()) == {
        "first": 1, "second": 1, "left": 1, "right": 1
    }


def test_failed_step_does_not_pollute_its_sibling_or_the_next_group() -> None:
    scenario = RuntimeScenario("failure cleanup")
    entered = Barrier(2)
    observed: list[str] = []

    def fail(env: ScenarioEnvironment) -> None:
        entered.wait(timeout=5)
        assert env.getArg("member") == "failed"
        raise ValueError("intentional callback failure")

    def sibling(env: ScenarioEnvironment) -> None:
        entered.wait(timeout=5)
        assert env.getArg("member") == "sibling"
        observed.append("sibling")

    def next_group(env: ScenarioEnvironment) -> None:
        assert env.getArgs() == ()
        assert env.get(ScenarioEnvironment.ARGUMENTS_KEY) == []
        observed.append("next group")

    scenario.Given("${member=failed}", Step.ContinuousAfterFailure, fail).And(
        "${member=sibling}", sibling
    ).When("no arguments in next group", next_group)

    with pytest.raises(EzSpecError, match="intentional callback failure"):
        scenario.ExecuteConcurrently()

    assert observed == ["sibling", "next group"]
    assert scenario.steps()[0].getResult().isFailure()
    assert scenario.steps()[1].getResult().isSuccess()
    assert scenario.steps()[2].getResult().isSuccess()
    env = scenario.getEnvironment()
    env.setArguments([Argument("${outside=fresh}")])
    assert env.getArg("outside") == "fresh"
    assert scenario.getEnvironment().getArgs() == env.getArgs()


def test_history_retains_every_concurrent_argument_after_the_group_finishes() -> None:
    scenario = RuntimeScenario("complete concurrent history")
    entered = Barrier(8)
    expected = Counter({f"member-{number}": 1 for number in range(8)})

    def member(env: ScenarioEnvironment) -> None:
        entered.wait(timeout=5)

    for number in range(8):
        register = scenario.Given if number == 0 else scenario.And
        register("${member=member-" + str(number) + "}", member)

    def verify(env: ScenarioEnvironment) -> None:
        assert Counter(arg.value() for arg in env.getHistoricalArgs()) == expected
        assert env.getArgs() == ()

    scenario.Then("history after joining the group", verify).ExecuteConcurrently()
    assert Counter(
        arg.value() for arg in scenario.getEnvironment().getHistoricalArgs()
    ) == expected


def test_next_group_inherits_last_declared_table_despite_callback_completion_order() -> None:
    scenario = RuntimeScenario("last declared table")
    last_declared_done = Event()
    completed: list[str] = []

    def first(env: ScenarioEnvironment) -> None:
        assert last_declared_done.wait(timeout=5)
        assert env.row(0).get("member") == "first"
        completed.append("first")

    def last(env: ScenarioEnvironment) -> None:
        assert env.row(0).get("member") == "last"
        completed.append("last")
        last_declared_done.set()

    def next_group(env: ScenarioEnvironment) -> None:
        assert completed == ["last", "first"]
        assert env.row(0).get("member") == "last"
        assert scenario.activeTable() is env.table()

    scenario.Given("first\n| member |\n| first |", first).And(
        "last\n| member |\n| last |", last
    ).But("no table after the explicit tables", lambda env: None).Then(
        "inherit the completed group's table", next_group
    ).ExecuteConcurrently()

    assert scenario.activeTable().row(0).get("member") == "last"
    assert scenario.getEnvironment().table() is scenario.activeTable()


def test_clone_and_add_context_see_the_source_callbacks_local_reserved_values() -> None:
    input_table = Table("| value |\n| original |")
    scenario = RuntimeScenario("copy active environment", table=input_table)
    entered = Barrier(2)
    shared_value = {"shared": True}
    scenario.getEnvironment().put("user data", shared_value)

    def member(name: str):
        def callback(env: ScenarioEnvironment) -> None:
            entered.wait(timeout=5)
            cloned = ScenarioEnvironment.clone(env)
            combined = ScenarioEnvironment.create()
            combined.addContext(env)

            assert cloned.getArgs() == ()
            assert combined.getArg("member") == name
            for copied in [cloned, combined]:
                assert copied.getInput() is input_table
                assert copied.get("user data") is shared_value
                assert copied.table() is env.table()
                assert copied.row(0).get("member") == name
                assert copied.get(ScenarioEnvironment.ANONYMOUS_TABLE_KEY) is env.table()
                assert Counter(arg.value() for arg in copied.getHistoricalArgs()) == {
                    "left": 1, "right": 1
                }

        return callback

    scenario.Given(
        "${member=left}\n| member |\n| left |", member("left")
    ).And(
        "${member=right}\n| member |\n| right |", member("right")
    ).ExecuteConcurrently()
