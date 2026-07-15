"""Scenario outlines assigned directly to user-created Rules."""

from ezspec import (
    EzFeature,
    EzScenarioOutline,
    Feature,
    ScenarioEnvironment,
    ScenarioOutline,
)
from ezspec.extension.pytest import PytestExamples


TAX_CALCULATION_TABLE = """
| tax_excluded | vat_rate | total_price |
| 20000        | 0.05     | 21000       |
| 10000        | 0.01     | 10100       |
| 35000        | 0.10     | 38500       |
"""

ZERO_DOLLAR_INVOICE_TABLE = """
| tax_excluded | vat_rate | total_price |
| 0            | 0.05     | 0           |
"""


class TaxCalculationExample(PytestExamples):
    def getDescription(self) -> str:
        return "Calculate tax."

    def getExamplesRawData(self) -> str:
        return TAX_CALCULATION_TABLE


class ZeroDollarInvoiceExample(PytestExamples):
    def getDescription(self) -> str:
        return "Zero dollar invoice."

    def getExamplesRawData(self) -> str:
        return ZERO_DOLLAR_INVOICE_TABLE


def remember_tax_excluded_input(env: ScenarioEnvironment) -> None:
    env.put("tax excluded price", env.getInput().get("tax_excluded"))


def remember_vat_rate_input(env: ScenarioEnvironment) -> None:
    env.put("vat rate", env.getInput().get("vat_rate"))


def calculate_tax_included_price(env: ScenarioEnvironment) -> None:
    price = env.geti("tax excluded price") * (1 + float(env.gets("vat rate")))
    env.put("tax included price", price)


def verify_tax_included_price(env: ScenarioEnvironment) -> None:
    expected = float(env.getInput().get("total_price"))
    assert expected == env.get("tax included price")


def add_tax_calculation_steps(outline: ScenarioOutline) -> ScenarioOutline:
    """Add the same named callbacks used by all three Java examples."""

    return (
        outline.Given(
            "the tax excluded price of a computer is <tax_excluded>",
            remember_tax_excluded_input,
        )
        .And("the VAT rate is <vat_rate>", remember_vat_rate_input)
        .When("I buy the computer", calculate_tax_included_price)
        .Then("I need to pay <total_price>", verify_tax_included_price)
    )


@EzFeature
class ScenarioOutlineExample:
    """Equivalent of ezspec-sample's named-rule ScenarioOutlineExample."""

    feature = Feature.New("scenario outline example")
    scenario_outline_with_table = feature.NewRule("scenario outline with table")
    scenario_outline_with_examples = feature.NewRule(
        "scenario outline with example"
    )

    @EzScenarioOutline
    def scenario_outline_example_with_table_input(self) -> None:
        outline = ScenarioOutline.New(self.scenario_outline_with_table).WithExamples(
            TAX_CALCULATION_TABLE
        )
        add_tax_calculation_steps(outline).Execute()

    @EzScenarioOutline
    def scenario_outline_example_with_variable_arguments(self) -> None:
        outline = ScenarioOutline.New(
            self.scenario_outline_with_examples
        ).WithExamples(
            PytestExamples.get(TaxCalculationExample),
            PytestExamples.get(ZeroDollarInvoiceExample),
        )
        add_tax_calculation_steps(outline).Execute()

    @EzScenarioOutline
    def scenario_outline_example_with_list_of_example(self) -> None:
        examples = [
            PytestExamples.get(TaxCalculationExample),
            PytestExamples.get(ZeroDollarInvoiceExample),
        ]

        outline = ScenarioOutline.New(
            self.scenario_outline_with_examples
        ).WithExamples(examples)
        add_tax_calculation_steps(outline).Execute()
