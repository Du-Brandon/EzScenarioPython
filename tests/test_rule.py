import pytest

from ezspec.feature import Feature
from ezspec.rule import Background, Rule


def test_rule_reuses_scenario_with_the_same_name():
    rule = Feature.New("Checkout").NewRule("VIP")

    first = rule.newScenario("discount")
    second = rule.newScenario("discount")

    assert first is second
    assert rule.getScenarios() == [first]


def test_rule_rejects_scenario_outline_name_collision():
    rule = Feature.New("Checkout").NewRule("VIP")
    rule.newScenario("discount")

    with pytest.raises(TypeError):
        rule.newScenarioOutline("discount")


def test_background_environment_is_available_to_rule_scenario():
    feature = Feature.New("Checkout")
    rule = feature.NewRule("VIP")
    background = rule.newBackground("registered VIP")

    background.Given("a VIP user", lambda env: env.put("member", "Teddy")).Execute()
    scenario = rule.newScenario("checkout")

    assert scenario.getEnvironment().gets("member") == "Teddy"
    assert rule.getBackground() is background
    assert "Background: registered VIP" in str(background)


def test_rule_empty_and_default_background_are_safe_sentinels():
    empty = Rule.Empty()

    assert empty.getFeature() is None
    assert empty.getBackground() is Background.DEFAULT


def test_later_background_replaces_previous_context_for_a_rule():
    feature = Feature.New("Background")
    rule = feature.NewRule("one background")

    first = feature.newBackground("first").withRule(rule)
    first.Given("first value", lambda env: env.put("first", "old")).Execute()

    second = feature.newBackground("second").withRule(rule)
    second.Given("second value", lambda env: env.put("second", "new")).Execute()

    observed: dict[str, object] = {}

    def verify(env):
        observed["first"] = env.get("first")
        observed["second"] = env.get("second")

    feature.newScenario("read background").withRule(rule).Then("verify", verify).Execute()

    assert observed == {"first": None, "second": "new"}
    assert rule.getBackground() is second


def test_rule_background_context_is_available_to_scenario_outline_rows():
    feature = Feature.New("Background")
    rule = feature.NewRule("outline background")
    feature.newBackground("shared").withRule(rule).Given(
        "shared user", lambda env: env.put("user", "Teddy")
    ).Execute()

    users: list[str] = []

    def capture(env):
        users.append(env.gets("user"))

    (
        feature.newScenarioOutline("outline")
        .withRule(rule)
        .WithExamples("| role |\n| Admin |\n| Staff |")
        .Then("background is shared with <role>", capture)
        .Execute()
    )

    assert users == ["Teddy", "Teddy"]
