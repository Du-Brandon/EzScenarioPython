from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from ezspec.keyword import Example, Feature
from ezspec.extension.pytest.registry import get_registry
from ezspec.report.decorators import ReportConfig
from ezspec.report.generator import generate_feature_report
from ezspec.report.outline_projection import merged_feature_dict, render_outline_text


class FakeConfig:
    def __init__(self) -> None:
        self.stash: dict[object, Any] = {}


class ReportFeature:
    feature = Feature.New("加法")


def _item(config: FakeConfig, label: str) -> SimpleNamespace:
    def outline() -> None:
        pass

    return SimpleNamespace(
        config=config,
        cls=ReportFeature,
        obj=outline,
        nodeid=f"test_sum.py::ReportFeature::outline[{label}]",
        callspec=SimpleNamespace(params={"_ezspec_case": label, "currency": "TWD"}),
    )


def _case(index: int, code: str) -> SimpleNamespace:
    return SimpleNamespace(
        example_index=0,
        row_index=index,
        index=index,
        id=code,
        headers=("example_code", "a"),
        values=(code, str(index + 1)),
    )


def _catalog() -> SimpleNamespace:
    return SimpleNamespace(
        to_examples=lambda: (
            Example("| example_code | a |\n| ADD01 | 1 |\n| ADD02 | 2 |"),
        )
    )


def _definition(name: str = "兩數相加") -> SimpleNamespace:
    scenario = ReportFeature.feature.newScenario("template")
    scenario.Given("數字 <a>", lambda env: None)
    return SimpleNamespace(
        getName=lambda: name,
        getDescription=lambda: "加法範例",
        steps=scenario.steps,
        rule=ReportFeature.feature.getDefaultRule(),
    )


def _phase(when: str, outcome: str) -> SimpleNamespace:
    return SimpleNamespace(
        when=when,
        outcome=outcome,
        duration=0.01,
        failed=outcome == "failed",
        longrepr="fixture exploded" if outcome == "failed" else "",
    )


def test_partial_selection_projects_all_examples_and_only_started_runtime() -> None:
    config = FakeConfig()
    registry = get_registry(config)
    first = _item(config, "ADD01")
    second = _item(config, "ADD02")
    registry.register_item(first, _catalog(), _case(0, "ADD01"))
    registry.register_item(second, _catalog(), _case(1, "ADD02"))
    registry.mark_selected([second])
    registry.begin_attempt(second)
    registry.record_phase(second, _phase("setup", "passed"))
    definition = _definition()
    registry.validate_definition(second, definition)
    runtime = ReportFeature.feature.newScenario("runtime")
    runtime.Given("數字 <2>", lambda env: None)
    runtime.Execute()
    registry.record_runtime(second, definition, runtime)
    registry.record_phase(second, _phase("call", "passed"))
    registry.record_phase(second, _phase("teardown", "passed"))

    snapshot = registry.feature_snapshot(ReportFeature)
    assert (snapshot["totalRows"], snapshot["selectedRows"], snapshot["completedRows"]) == (2, 1, 1)
    assert snapshot["items"][0]["attemptCount"] == 0
    assert snapshot["items"][1]["attemptCount"] == 1
    report = merged_feature_dict(ReportFeature.feature, snapshot)
    outline = report["ruleDtos"][0]["specificationElementDtos"][-1]
    assert len(outline["allExampleDtos"][0]["tableDto"]["rows"]) == 2
    assert len(outline["runtimeScenarioDtos"]) == 1
    assert outline["runtimeScenarioDtos"][0]["stepDtos"][0]["stepExecutionOutcome"] == "Success"
    text = render_outline_text(snapshot, language="zh-TW")
    assert "共 2 列／選取 1 列" in text
    assert "假如 數字 <a>" in text
    assert "[Success] 假如 數字 <2>" in text


def test_setup_failure_does_not_count_as_started_or_completed() -> None:
    config = FakeConfig()
    registry = get_registry(config)
    item = _item(config, "ADD01")
    registry.register_item(item, _catalog(), _case(0, "ADD01"))
    registry.mark_selected([item])
    registry.begin_attempt(item)
    registry.record_phase(item, _phase("setup", "failed"))
    registry.record_phase(item, _phase("teardown", "passed"))
    snapshot = registry.feature_snapshot(ReportFeature)
    assert snapshot["startedRows"] == 0
    assert snapshot["completedRows"] == 0
    assert snapshot["items"][0]["attemptCount"] == 1
    assert snapshot["items"][0]["attempts"][0]["phases"]["setup"]["outcome"] == "failed"


def test_header_only_is_explicit_zero_row_no_op() -> None:
    config = FakeConfig()
    registry = get_registry(config)
    item = _item(config, "no-examples")
    catalog = SimpleNamespace(to_examples=lambda: (Example("| a |"),))
    registry.register_item(item, catalog, None)
    registry.mark_selected([item])
    registry.begin_attempt(item)
    registry.record_phase(item, _phase("setup", "passed"))
    registry.record_phase(item, _phase("call", "passed"))
    registry.record_phase(item, _phase("teardown", "passed"))
    snapshot = registry.feature_snapshot(ReportFeature)
    assert (snapshot["totalRows"], snapshot["startedRows"], snapshot["completedRows"]) == (0, 0, 0)
    assert "0 列，未執行步驟" in render_outline_text(snapshot, language="en")


@pytest.mark.parametrize(
    ("phases", "expected"),
    [
        ((("setup", "failed"), ("teardown", "passed")), "pytest setup: failed"),
        ((("setup", "skipped"), ("teardown", "passed")), "pytest setup: skipped"),
        (
            (("setup", "passed"), ("call", "passed"), ("teardown", "failed")),
            "pytest teardown: failed",
        ),
        (
            (("setup", "passed"), ("call", "passed"), ("teardown", "skipped")),
            "pytest teardown: skipped",
        ),
    ],
)
def test_header_only_preserves_fixture_phase_outcomes(
    phases: tuple[tuple[str, str], ...], expected: str,
) -> None:
    config = FakeConfig()
    registry = get_registry(config)
    item = _item(config, "no-examples")
    catalog = SimpleNamespace(to_examples=lambda: (Example("| a |"),))
    registry.register_item(item, catalog, None)
    registry.mark_selected([item])
    registry.begin_attempt(item)
    for when, outcome in phases:
        registry.record_phase(item, _phase(when, outcome))

    snapshot = registry.feature_snapshot(ReportFeature)
    assert (
        snapshot["totalRows"], snapshot["selectedRows"],
        snapshot["startedRows"], snapshot["completedRows"],
    ) == (0, 0, 0, 0)
    for text in (
        registry.format_item_steps(item),
        render_outline_text(snapshot, language="en"),
    ):
        assert "0 列，未執行步驟" in text
        assert expected in text
        assert "[Success]" not in text


def test_template_mismatch_is_rejected_before_callbacks() -> None:
    config = FakeConfig()
    registry = get_registry(config)
    first = _item(config, "ADD01")
    second = _item(config, "ADD02")
    registry.register_item(first, _catalog(), _case(0, "ADD01"))
    registry.register_item(second, _catalog(), _case(1, "ADD02"))
    registry.validate_definition(first, _definition())
    with pytest.raises(ValueError, match="declaration differs"):
        registry.validate_definition(second, _definition("不同名稱"))


def test_equal_pytest_parameter_values_from_different_indices_stay_separate() -> None:
    config = FakeConfig()
    registry = get_registry(config)
    first = _item(config, "same-0-ADD01")
    second = _item(config, "same-1-ADD01")
    first.callspec.indices = {"currency": 0, "_ezspec_case": 0}
    second.callspec.indices = {"currency": 1, "_ezspec_case": 0}
    registry.register_item(first, _catalog(), _case(0, "ADD01"))
    registry.register_item(second, _catalog(), _case(0, "ADD01"))
    assert len(registry.feature_snapshot(ReportFeature)["groups"]) == 2


def test_rerun_keeps_attempt_phases_separate() -> None:
    config = FakeConfig()
    registry = get_registry(config)
    item = _item(config, "ADD01")
    registry.register_item(item, _catalog(), _case(0, "ADD01"))
    registry.begin_attempt(item)
    registry.record_phase(item, _phase("setup", "failed"))
    registry.record_phase(item, _phase("teardown", "passed"))
    registry.begin_attempt(item)
    registry.record_phase(item, _phase("setup", "passed"))
    registry.validate_definition(item, _definition())
    registry.record_phase(item, _phase("call", "passed"))
    registry.record_phase(item, _phase("teardown", "passed"))
    item_snapshot = registry.feature_snapshot(ReportFeature)["items"][0]
    assert item_snapshot["attemptCount"] == 2
    assert item_snapshot["attempts"][0]["started"] is False
    assert item_snapshot["attempts"][1]["started"] is True
    assert item_snapshot["attempts"][1]["completed"] is True


def test_text_report_keeps_each_outline_rule_and_existing_backgrounds(tmp_path) -> None:
    class RuleFeature:
        feature = Feature.New("rule scopes")

    first_rule = RuleFeature.feature.NewRule("first rule")
    second_rule = RuleFeature.feature.NewRule("second rule")
    first_rule.newBackground("first background").Given("first prerequisite", lambda env: None)
    second_rule.newBackground("second background").Given("second prerequisite", lambda env: None)
    config = FakeConfig()
    registry = get_registry(config)
    for method, rule in (
        ("first_outline", first_rule),
        ("second_outline", second_rule),
        ("default_outline", RuleFeature.feature.getDefaultRule()),
    ):
        item = _item(config, "ADD01")
        item.cls = RuleFeature
        item.nodeid = f"test_rule.py::RuleFeature::{method}[ADD01]"
        item.originalname = method
        definition = RuleFeature.feature.defineScenarioOutline(method)
        if rule is not RuleFeature.feature.getDefaultRule():
            definition.withRule(rule)
        registry.register_item(item, _catalog(), _case(0, "ADD01"))
        registry.validate_definition(item, definition)

    snapshot = registry.feature_snapshot(RuleFeature)
    paths = generate_feature_report(
        RuleFeature, ReportConfig(formats=("txt",)),
        output_dir=tmp_path, execution_snapshot=snapshot,
    )
    text = paths[0].read_text(encoding="utf-8")
    assert "Background: first background\nGiven first prerequisite" in text
    assert "Background: second background\nGiven second prerequisite" in text
    assert "Rule: first rule\nScenario Outline: first_outline" in text
    assert "Rule: second rule\nScenario Outline: second_outline" in text
    assert "Rule: (default)\nScenario Outline: default_outline" in text
    assert all(not rule.getScenarios() for rule in RuleFeature.feature.getRules())
    assert not RuleFeature.feature.getDefaultRule().getScenarios()


def test_same_named_outlines_show_method_and_pytest_parameters() -> None:
    config = FakeConfig()
    registry = get_registry(config)
    for method, currency, index in (
        ("purchase", "TWD", 0),
        ("purchase", "USD", 1),
        ("refund", "TWD", 0),
    ):
        item = _item(config, f"{method}-{currency}-ADD01")
        item.originalname = method
        item.obj = SimpleNamespace(__module__="test_money", __qualname__=f"MoneyFeature.{method}")
        item.callspec.params["currency"] = currency
        item.callspec.indices = {"currency": index, "_ezspec_case": 0}
        registry.register_item(item, _catalog(), _case(0, "ADD01"))
        registry.validate_definition(item, _definition("same outline"))

    text = render_outline_text(registry.feature_snapshot(ReportFeature), language="en")
    blocks = text.split("Scenario Outline: same outline\n")[1:]
    assert len(blocks) == 3
    assert 'Source: test_money.MoneyFeature.purchase\npytest parameters: {"currency": "TWD"}' in blocks[0]
    assert 'Source: test_money.MoneyFeature.purchase\npytest parameters: {"currency": "USD"}' in blocks[1]
    assert 'Source: test_money.MoneyFeature.refund\npytest parameters: {"currency": "TWD"}' in blocks[2]
