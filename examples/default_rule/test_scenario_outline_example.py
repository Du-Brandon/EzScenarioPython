"""Port of ezspec-sample's default-rule Scenario Outline examples."""

from __future__ import annotations

from math import isclose

from ezspec import (
    EzFeature,
    EzScenarioOutline,
    Feature,
    Header,
    ScenarioEnvironment,
    Table,
)
from ezspec.extension.pytest import PytestExamples


TAX_CALCULATION_RAW_DATA = """
| tax_excluded | vat_rate | total_price |
| 20000        | 0.05     | 21000       |
| 10000        | 0.01     | 10100       |
| 35000        | 0.10     | 38500       |
"""

ZERO_DOLLAR_INVOICE_RAW_DATA = """
| tax_excluded | vat_rate | total_price |
| 0            | 0.05     | 0           |
"""

GIVEN_WORKFLOW = """
| lane_name | lane_id | parent_id | lane_layout | wip_limit |
| To Do     | root1   | -1        | Vertical    | 3         |
| Doing     | root2   | -1        | Vertical    | 5         |
| Done      | root3   | -1        | Vertical    | -1        |
"""

EXPECTED_ROOT_STAGE_TO_MIDDLE = """
| lane_name | lane_id | parent_id | lane_layout | wip_limit |
| Doing     | root2   | -1        | Vertical    | 5         |
| To Do     | root1   | -1        | Vertical    | 3         |
| Done      | root3   | -1        | Vertical    | -1        |
"""

EXPECTED_ROOT_STAGE_TO_LAST = """
| lane_name | lane_id | parent_id | lane_layout | wip_limit |
| Doing     | root2   | -1        | Vertical    | 5         |
| Done      | root3   | -1        | Vertical    | -1        |
| To Do     | root1   | -1        | Vertical    | 3         |
"""


class tax_calculation_examples(PytestExamples):
    def getDescription(self) -> str:
        return "Calculate tax."

    def getExamplesRawData(self) -> str:
        return TAX_CALCULATION_RAW_DATA


class zero_dollar_invoice_examples(PytestExamples):
    def getDescription(self) -> str:
        return "Zero dollar invoice."

    def getExamplesRawData(self) -> str:
        return ZERO_DOLLAR_INVOICE_RAW_DATA


class change_root_stage_order_examples(PytestExamples):
    HEADER = (
        "example_code",
        "lane_name",
        "new_parent_name",
        "new_position",
        "event_count",
        "given_workflow",
        "expected_workflow",
    )

    def getDescription(self) -> str:
        return "The order of root stages can be changed."

    def getExamplesRawData(self) -> str:
        # Nested tables require programmatic construction, just as in Java.
        return str(self.getTable())

    def getTable(self) -> Table:
        table = Table(Header.valueOf(self.HEADER))
        table.addRow(
            (
                "ML-D01",
                "To Do",
                "Workflow",
                "1",
                "1",
                GIVEN_WORKFLOW,
                EXPECTED_ROOT_STAGE_TO_MIDDLE,
            )
        )
        table.addRow(
            (
                "ML-D02",
                "To Do",
                "Workflow",
                "2",
                "1",
                GIVEN_WORKFLOW,
                EXPECTED_ROOT_STAGE_TO_LAST,
            )
        )
        return table


def remember_tax_excluded_price(env: ScenarioEnvironment) -> None:
    inputs = env.getInput()
    assert inputs is not None
    env.put("tax excluded price", inputs.get("tax_excluded"))


def remember_vat_rate(env: ScenarioEnvironment) -> None:
    inputs = env.getInput()
    assert inputs is not None
    env.put("vat rate", inputs.get("vat_rate"))


def calculate_tax_included_price(env: ScenarioEnvironment) -> None:
    price = env.geti("tax excluded price") * (1 + float(env.gets("vat rate")))
    env.put("tax included price", price)


def verify_total_price(env: ScenarioEnvironment) -> None:
    inputs = env.getInput()
    assert inputs is not None
    expected = float(inputs.get("total_price"))
    assert isclose(expected, env.get("tax included price"))


def remember_workflow(env: ScenarioEnvironment) -> None:
    workflow = env.get("given_workflow")
    assert isinstance(workflow, Table)
    assert workflow.header().header() == (
        "lane_name",
        "lane_id",
        "parent_id",
        "lane_layout",
        "wip_limit",
    )
    env.put("workflow rows", [row.columns() for row in workflow.rows()])


def move_lane(env: ScenarioEnvironment) -> None:
    assert env.gets("new_parent_name") == "Workflow"
    inputs = env.getInput()
    assert inputs is not None
    assert int(inputs.get("event_count")) == 1

    rows = env.get("workflow rows")
    lane_name = env.gets("lane_name")
    moved_row = next(row for row in rows if row[0] == lane_name)
    rows.remove(moved_row)
    rows.insert(env.geti("new_position"), moved_row)


def verify_workflow(env: ScenarioEnvironment) -> None:
    expected = env.get("expected_workflow")
    assert isinstance(expected, Table)
    assert env.get("workflow rows") == [row.columns() for row in expected.rows()]


@EzFeature
class ScenarioOutlineExample:
    feature = Feature.New("scenario outline example")

    @EzScenarioOutline
    def scenario_outline_example_with_table_input(self) -> None:
        (
            self.feature.newScenarioOutline()
            .WithExamples(TAX_CALCULATION_RAW_DATA)
            .Given(
                "the tax excluded price of a computer is <tax_excluded>",
                remember_tax_excluded_price,
            )
            .And("the VAT rate is <vat_rate>", remember_vat_rate)
            .When("I buy the computer", calculate_tax_included_price)
            .Then("I need to pay <total_price>", verify_total_price)
            .Execute()
        )

    @EzScenarioOutline
    def scenario_outline_example_with_variable_arguments(self) -> None:
        (
            self.feature.newScenarioOutline()
            .WithExamples(
                PytestExamples.get(tax_calculation_examples),
                PytestExamples.get(zero_dollar_invoice_examples),
            )
            .Given(
                "the tax excluded price of a computer is <tax_excluded>",
                remember_tax_excluded_price,
            )
            .And("the VAT rate is <vat_rate>", remember_vat_rate)
            .When("I buy the computer", calculate_tax_included_price)
            .Then("I need to pay <total_price>", verify_total_price)
            .Execute()
        )

    @EzScenarioOutline
    def scenario_outline_example_with_list_of_example(self) -> None:
        examples = [
            PytestExamples.get(tax_calculation_examples),
            PytestExamples.get(zero_dollar_invoice_examples),
        ]

        (
            self.feature.newScenarioOutline()
            .WithExamples(examples)
            .Given(
                "the tax excluded price of a computer is <tax_excluded>",
                remember_tax_excluded_price,
            )
            .And("the VAT rate is <vat_rate>", remember_vat_rate)
            .When("I buy the computer", calculate_tax_included_price)
            .Then("I need to pay <total_price>", verify_total_price)
            .Execute()
        )

    @EzScenarioOutline
    def moving_root_stages_and_sub_lanes(self) -> None:
        (
            self.feature.newScenarioOutline()
            .WithExamples(PytestExamples.get(change_root_stage_order_examples))
            .Given("the following workflow:\n <given_workflow>", remember_workflow)
            .When(
                "I move <lane_name> to position <new_position> "
                "under <new_parent_name>",
                move_lane,
            )
            .Then(
                "the workflow looks like the following:\n<expected_workflow>",
                verify_workflow,
            )
            .Execute()
        )
