import json

import pytest

from ezspec.exception import EzSpecError, PendingException
from ezspec.keyword import Example, Feature
from ezspec.report.dto import FeatureDto
from ezspec.report.json_report import render_json


def _build_report_feature() -> Feature:
    feature = Feature.New("購物車報表", "以中文驗證 JSON schema")

    background = feature.newBackground("共用前置")

    def prepare_customer(env):
        env.put("customer", "Teddy")

    background.Given("已有顧客", prepare_customer).Execute()

    default_scenario = feature.newScenario("一般結帳")

    def complete_checkout(env):
        assert env.gets("customer") == "Teddy"

    default_scenario.When("完成結帳", complete_checkout).Execute()

    vip_rule = feature.NewRule("VIP 規則", "VIP 顧客享有折扣")
    outline = vip_rule.newScenarioOutline("依等級折扣", "每個等級各執行一次")
    examples = Example(
        "會員等級",
        "不同折扣",
        "| level | total |\n| gold | 900 |\n| silver | 950 |",
    )

    def verify_total(env):
        assert env.gets("total") in {"900", "950"}

    outline.WithExamples(examples).Then("總額是 <total>", verify_total).Execute()
    return feature


def test_feature_dto_preserves_java_schema_for_complete_feature_tree():
    dto = FeatureDto.from_feature(_build_report_feature())
    report = dto.to_dict()

    assert FeatureDto.of(_build_report_feature()).to_dict() == report
    assert report["keyword"] == "Feature"
    assert report["name"] == "購物車報表"
    assert [rule["name"] for rule in report["ruleDtos"]] == ["", "VIP 規則"]

    default_rule, named_rule = report["ruleDtos"]
    assert default_rule["backgroundDto"] == {
        "keyword": "Background",
        "name": "共用前置",
        "stepDtos": [
            {
                "keyword": "Given",
                "description": "已有顧客",
                "stepExecutionOutcome": "Success",
                "errorMessage": "",
                "exception": "",
                "stackTrace": "",
                "continuousAfterFailure": False,
            }
        ],
    }
    assert default_rule["specificationElementDtos"][0]["@class"] == "ScenarioDto"

    outline = named_rule["specificationElementDtos"][0]
    assert outline["@class"] == "ScenarioOutlineDto"
    assert outline["rawStepDtos"][0]["stepExecutionOutcome"] == "Pending"
    assert [
        scenario["stepDtos"][0]["stepExecutionOutcome"]
        for scenario in outline["runtimeScenarioDtos"]
    ] == ["Success", "Success"]
    assert outline["allExampleDtos"][0]["tableDto"] == {
        "headerDto": {"header": ["level", "total"]},
        "rows": [
            {"columns": ["gold", "900"]},
            {"columns": ["silver", "950"]},
        ],
        "RawData": "| level | total |\n| gold | 900 |\n| silver | 950 |",
    }


def test_step_dto_records_failure_and_pending_details():
    feature = Feature.New("錯誤狀態")
    scenario = feature.newScenario("失敗與待辦")

    def fail_step(env):
        raise AssertionError("報表失敗")

    def pending_step(env):
        raise PendingException("尚未實作")

    scenario.Then("應該失敗", True, fail_step).And("等待實作", pending_step)
    with pytest.raises(EzSpecError):
        scenario.Execute()

    steps = FeatureDto.of(feature).to_dict()["ruleDtos"][0][
        "specificationElementDtos"
    ][0]["stepDtos"]

    assert steps[0]["stepExecutionOutcome"] == "Failure"
    assert steps[0]["exception"] == "AssertionError: 報表失敗"
    assert steps[0]["errorMessage"].endswith("[報表失敗]")
    assert "fail_step" in steps[0]["stackTrace"]
    assert steps[0]["continuousAfterFailure"] is True
    assert steps[1]["stepExecutionOutcome"] == "Pending"
    assert steps[1]["errorMessage"] == "[尚未實作]"
    assert steps[1]["exception"] == "ezspec.exception.errors.PendingException: 尚未實作"


def test_render_json_is_compact_unicode_json_and_supports_indentation():
    feature = _build_report_feature()

    compact = render_json(feature)
    pretty = render_json(FeatureDto.of(feature), indent=2)

    assert '"name":"購物車報表"' in compact
    assert "\\u8cfc" not in compact
    assert ": " not in compact
    assert "\n  \"keyword\": \"Feature\"" in pretty
    assert json.loads(compact) == json.loads(pretty)
