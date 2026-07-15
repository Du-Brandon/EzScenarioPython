import pytest

from ezspec.examples import Example
from ezspec.exceptions import EzSpecError
from ezspec.feature import Feature
from ezspec.scenario_outline import ScenarioOutline


EXAMPLES = """
| price | rate | total |
| 1000  | 0.1  | 900   |
| 2000  | 0.2  | 1600  |
"""


def test_outline_builds_one_runtime_scenario_per_example_row():
    outline = Feature.New("Checkout").newScenarioOutline("VIP discount")

    result = outline.WithExamples(EXAMPLES)

    assert result is outline
    assert len(outline.getAllExamples()) == 1
    assert len(outline.RuntimeScenarios()) == 2
    assert outline.RuntimeScenarios()[1].getEnvironment().getInput().get("total") == "1600"


def test_outline_executes_each_row_and_replaces_step_variables():
    seen: list[tuple[str, int]] = []
    outline = Feature.New("Checkout").newScenarioOutline("VIP discount")

    def verify(env):
        seen.append((env.gets("price"), env.getExecutionCount()))
        assert env.gets("total") in {"900", "1600"}

    outline.WithExamples(EXAMPLES).Then(
        "<price> discounted total is <total>", verify
    ).Execute()

    assert seen == [("1000", 1), ("2000", 2)]
    assert outline.RuntimeScenarios()[0].steps()[0].description() == (
        "<1000> discounted total is <900>"
    )
    assert outline.RuntimeScenarios()[1].steps()[0].description() == (
        "<2000> discounted total is <1600>"
    )


def test_outline_accepts_multiple_named_examples():
    first = Example("first", "", "| value |\n| A |")
    second = Example("second", "", "| value |\n| B |\n| C |")
    outline = Feature.New("Values").newScenarioOutline("all values")

    outline.WithExamples(first, second)

    assert len(outline.RuntimeScenarios()) == 3
    assert [example.getName() for example in outline.getAllExamples()] == [
        "first",
        "second",
    ]


def test_outline_requires_examples_and_ignores_second_assignment():
    outline = Feature.New("Values").newScenarioOutline("all values")
    with pytest.raises(RuntimeError, match="at least an example"):
        outline.WithExamples([])

    outline.WithExamples("| value |\n| A |")
    outline.WithExamples("| value |\n| B |\n| C |")
    assert len(outline.RuntimeScenarios()) == 1


def test_outline_without_examples_has_no_runtime_scenarios_and_execute_is_noop():
    called = False
    outline = Feature.New("Values").newScenarioOutline("all values")

    def should_not_run(env):
        nonlocal called
        called = True

    outline.Then("nothing runs without examples", should_not_run).Execute()

    assert outline.RuntimeScenarios() == ()
    assert called is False


def test_outline_collects_failures_after_running_all_rows():
    count = 0
    outline = Feature.New("Checkout").newScenarioOutline("VIP discount")

    def fail(env):
        nonlocal count
        count += 1
        raise AssertionError(env.gets("price"))

    outline.WithExamples(EXAMPLES).Then("price <price>", fail)

    with pytest.raises(EzSpecError):
        outline.Execute()
    assert count == 2


def test_outline_renders_template_and_examples():
    outline = Feature.New("Checkout").newScenarioOutline(
        "VIP_discount", "Discount depends on membership"
    )
    outline.WithExamples(EXAMPLES).Given("a cart of <price>", lambda env: None)

    text = str(outline)
    assert text.startswith(
        "Scenario Outline: VIP discount\n\nDiscount depends on membership\n"
    )
    assert "Given a cart of <price>" in text
    assert "Examples: " in text


def test_static_outline_factory_uses_calling_function_name():
    rule = Feature.New("Checkout").NewRule("VIP")

    def vip_discount_examples():
        return ScenarioOutline.New(rule)

    outline = vip_discount_examples()

    assert outline.getName() == "vip_discount_examples"
