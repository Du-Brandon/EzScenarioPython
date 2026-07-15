from __future__ import annotations

import threading

import pytest

from ezspec.exceptions import EzSpecError, PendingException
from ezspec.scenario import RuntimeScenario
from ezspec.step import Step


def test_scenario_executes_callbacks_sequentially_with_one_environment() -> None:
    calls: list[str] = []
    scenario = RuntimeScenario("checkout_succeeds")

    def prepare(env) -> None:
        calls.append("given")
        env.put("price", 1000)

    def checkout(env) -> None:
        calls.append("when")
        env.put("total", env.get("price") * 0.9)

    def verify(env) -> None:
        calls.append("then")
        assert env.get("total") == 900

    result = (
        scenario.Given("a cart", prepare)
        .When("checkout", checkout)
        .Then("the discounted total", verify)
    )
    result.Execute()

    assert result is scenario
    assert calls == ["given", "when", "then"]
    assert all(step.getResult().isSuccess() for step in scenario.steps())


def test_step_arguments_and_table_are_available_only_when_callback_runs() -> None:
    scenario = RuntimeScenario("arguments")

    def verify(env) -> None:
        assert env.getArg("VAT") == "5%"
        assert env.row(0).get("owner") == "Jill"

    scenario.Given(
        """VAT is ${VAT=5%}
        | owner | points |
        | Jill  | 100    |""",
        verify,
    ).Execute()


def test_fail_fast_marks_remaining_steps_skipped_and_raises_original_error() -> None:
    scenario = RuntimeScenario("fail fast")

    def fail(_env) -> None:
        raise ValueError("broken")

    scenario.Given("failed", fail).When("not run", lambda _env: None)

    with pytest.raises(ValueError, match="broken"):
        scenario.Execute()

    assert scenario.steps()[0].getResult().isFailure()
    assert scenario.steps()[1].getResult().isSkipped()


def test_continuous_failures_are_aggregated_after_all_steps_run() -> None:
    scenario = RuntimeScenario("collect failures")

    def first(_env) -> None:
        raise ValueError("first")

    def second(_env) -> None:
        raise AssertionError("second")

    scenario.Given("first", Step.ContinuousAfterFailure, first).Then(
        "second", Step.ContinuousAfterFailure, second
    )

    with pytest.raises(EzSpecError) as error:
        scenario.Execute()

    assert "first" in str(error.value)
    assert "second" in str(error.value)
    assert all(step.getResult().isFailure() for step in scenario.steps())


def test_pending_step_does_not_fail_or_stop_the_scenario() -> None:
    calls: list[str] = []
    scenario = RuntimeScenario("pending")

    def pending(_env) -> None:
        PendingException.pending("waiting")

    scenario.Given("not implemented", pending).Then(
        "still runs", lambda _env: calls.append("then")
    ).Execute()

    assert scenario.steps()[0].getResult().isPending()
    assert scenario.steps()[1].getResult().isSuccess()
    assert calls == ["then"]


def test_then_success_and_failure_support_all_java_overloads() -> None:
    callback = lambda _env: None
    scenario = RuntimeScenario("overloads")

    scenario.ThenSuccess(callback)
    scenario.ThenSuccess(True, callback)
    scenario.ThenSuccess("description", callback)
    scenario.ThenFailure("description", True, callback)
    scenario.Execute()

    assert [step.description() for step in scenario.steps()] == [
        "",
        "",
        "description",
        "description",
    ]
    assert [step.isContinuousAfterFailure() for step in scenario.steps()] == [
        False,
        True,
        False,
        True,
    ]


def test_concurrent_group_completes_before_next_group_starts() -> None:
    scenario = RuntimeScenario("concurrent")
    barrier = threading.Barrier(3)
    completed: list[str] = []

    def member(name: str):
        def callback(_env) -> None:
            barrier.wait(timeout=2)
            completed.append(name)

        return callback

    scenario.Given("prepare", lambda _env: completed.append("prepare"))
    scenario.Then("member one", member("one"))
    scenario.And("member two", member("two"))
    scenario.But("member three", member("three"))

    def verify(_env) -> None:
        assert set(completed) == {"prepare", "one", "two", "three"}

    scenario.When("next group", verify).ExecuteConcurrently()

    assert all(step.getResult().isSuccess() for step in scenario.steps())


def test_concurrent_fail_fast_waits_for_group_then_skips_later_groups() -> None:
    scenario = RuntimeScenario("concurrent fail fast")
    sibling_ran = threading.Event()

    def fail(_env) -> None:
        raise AssertionError("failed member")

    scenario.Given("group", lambda _env: None)
    scenario.Then("failure", fail)
    scenario.And("sibling", lambda _env: sibling_ran.set())
    scenario.When("later group", lambda _env: None)

    with pytest.raises(EzSpecError, match="failed member"):
        scenario.ExecuteConcurrently()

    assert sibling_ran.is_set()
    assert scenario.steps()[1].getResult().isFailure()
    assert scenario.steps()[2].getResult().isSuccess()
    assert scenario.steps()[3].getResult().isSkipped()


def test_concurrent_scenario_must_start_with_a_group_keyword() -> None:
    scenario = RuntimeScenario("invalid concurrent")
    scenario.And("orphan", lambda _env: None)

    with pytest.raises(RuntimeError, match="must start with a Given, When, or Then"):
        scenario.ExecuteConcurrently()

    assert scenario.steps()[0].getResult().isPending()


def test_scenario_plain_text_uses_display_name_and_erases_argument_markers() -> None:
    scenario = RuntimeScenario("paying_the_bill")
    scenario.Given("the total is ${total=100}", lambda _env: None).ThenSuccess(
        lambda _env: None
    )

    assert str(scenario) == (
        "Scenario: paying the bill\n"
        "Given the total is 100\n"
        "Then success\n"
    )
