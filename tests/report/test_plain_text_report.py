from __future__ import annotations

import pytest

from ezspec import Feature, PendingException, ScenarioEnvironment
from ezspec.keyword import Step
from ezspec.report.i18n import get_gherkin_keywords
from ezspec.report.plain_text import PlainTextReport, render_text


def _success(_environment: ScenarioEnvironment) -> None:
    pass


def _pending(_environment: ScenarioEnvironment) -> None:
    PendingException.pending("not implemented")


def _failure(_environment: ScenarioEnvironment) -> None:
    raise AssertionError("expected: total")


def test_plain_text_report_is_a_feature_visitor() -> None:
    feature = Feature.New("Checkout", "Customers can buy their cart.")
    rule = feature.NewRule("VIP", "VIP customers receive a discount.")
    background = rule.newBackground("signed_in")
    background.Given("the customer is signed in", _success).Execute()
    scenario = rule.newScenario("vip_checkout")
    scenario.Given("a cart", _success).And("a VIP account", _success).When(
        "checkout", _success
    ).Then("the total is discounted", _success).Execute()

    report = PlainTextReport()
    feature.accept(report)

    assert report.getOutput() == "\n".join(
        [
            "Feature: Checkout",
            "Customers can buy their cart.",
            "",
            "Rule: VIP",
            "VIP customers receive a discount.",
            "",
            "Background: signed in",
            "Given the customer is signed in",
            "[Success] Given the customer is signed in",
            "",
            "Scenario: vip checkout",
            "[Success] Given a cart",
            "[Success] And a VIP account",
            "[Success] When checkout",
            "[Success] Then the total is discounted",
        ]
    )


def test_render_text_localizes_traditional_chinese_aliases() -> None:
    feature = Feature.New("結帳")
    rule = feature.NewRule("VIP")
    scenario = rule.newScenario("折扣")
    scenario.Given("有一個購物車", _success).When("結帳", _success).Then(
        "顯示折扣", _success
    ).Execute()

    rendered = render_text(feature, language="zh-TW")

    assert rendered == render_text(feature, language="tw")
    assert "功能: 結帳" in rendered
    assert "規則: VIP" in rendered
    assert "場景: 折扣" in rendered
    assert "[Success] 假如 有一個購物車" in rendered
    assert "[Success] 當 結帳" in rendered
    assert "[Success] 那麼 顯示折扣" in rendered


def test_scenario_outline_renders_template_examples_and_runtime_rows() -> None:
    feature = Feature.New("Discount")
    outline = feature.newScenarioOutline("role_discount", "Discount by role.")
    outline.WithExamples(
        """
        | role | rate |
        | VIP  | 0.9  |
        | Staff| 0.8  |
        """
    )
    outline.When("the <role> customer checks out", _success).Then(
        "the rate is <rate>", _success
    ).Execute()

    rendered = render_text(feature)

    assert "Scenario Outline: role discount" in rendered
    assert "When the <role> customer checks out" in rendered
    assert "Examples:" in rendered
    assert "|\trole\t|\trate\t|" in rendered
    assert "[1]\n[Success] When the <VIP> customer checks out" in rendered
    assert "[2]\n[Success] When the <Staff> customer checks out" in rendered


def test_failure_pending_and_skipped_details_are_rendered() -> None:
    feature = Feature.New("Outcomes")
    failing = feature.newScenario("failure")
    failing.Given("a broken step", _failure).Then("not reached", _success)
    with pytest.raises(AssertionError):
        failing.Execute()

    pending = feature.newScenario("pending")
    pending.Given(
        "unfinished",
        Step.ContinuousAfterFailure,
        _pending,
    ).Then("still runs", _success).Execute()

    rendered = render_text(feature)

    assert "[Failure] Given a broken step" in rendered
    assert "\t\t\tat " in rendered
    assert "[anticipated: total]" in rendered
    assert "[Skipped] Then not reached" in rendered
    assert "[Pending] Given unfinished" in rendered
    assert "\t\t\tcaused by [not implemented]" in rendered
    assert "[Success] Then still runs" in rendered


def test_unknown_language_and_keyword_fail_clearly() -> None:
    with pytest.raises(ValueError, match="Unsupported report language"):
        get_gherkin_keywords("fr")

    with pytest.raises(ValueError, match="Unsupported Gherkin keyword"):
        get_gherkin_keywords("en").getI18nKeyword("Unknown")
