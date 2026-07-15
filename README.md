# EzScenarioPython

EzScenarioPython is a Python port of ezSpec 2.0.4's developer-facing BDD
internal DSL. It keeps the original Feature, Rule, Scenario, Given, When, Then,
and Execute vocabulary while integrating with pytest.

The Java reference source is pinned to commit
`061eadc8dd47510bf12d62dd87d3fdaa0a37b20d` in the sibling
`../ezspec-java-reference/` clone.

## Requirements

- Python 3.11 or newer
- pytest 8 or newer for test collection

## Development setup

```powershell
python -m pip install -e ".[dev]"
python -m pytest
```

## Executable samples

The Java `ezspec-sample` module is represented by executable specifications
under `examples/`. Run them independently with:

```powershell
python -m pytest examples -q
```

They cover Scenario and Scenario Outline usage with both the default Rule and
named Rules. The outline samples also demonstrate raw tables, reusable
`PytestExamples`, lists of examples, and nested tables.

```python
from ezspec.extension.pytest import PytestExamples


class tax_calculation_examples(PytestExamples):
    def getDescription(self) -> str:
        return "Calculate tax."

    def getExamplesRawData(self) -> str:
        return """
        | tax_excluded | vat_rate | total_price |
        | 20000        | 0.05     | 21000       |
        """
```

## Package layout

The public API remains available directly from `ezspec`, while the internal
layout follows ezSpec's concepts in a Python-friendly package structure:

```text
ezspec/
├── keyword/          # Feature, Rule, Scenario, Step, Table, and visitors
├── exception/        # execution and pending-step exceptions
├── extension/
│   └── pytest/       # decorators and pytest collection hooks
└── runtime_context.py
```

For normal specifications, prefer the concise public imports:

```python
from ezspec import Feature, Given, ScenarioEnvironment
```

Canonical subpackage imports are also supported for framework integration or
library development:

```python
from ezspec.exception import PendingException
from ezspec.extension.pytest import EzFeature, EzScenario
from ezspec.keyword import Feature, ScenarioEnvironment
from ezspec.keyword.table import Table
```

The former flat module paths, such as `ezspec.feature` and
`ezspec.pytest_plugin`, remain as compatibility shims.

## Living-documentation reports

Generate TXT and Java-schema-compatible JSON reports for all collected
ezSpec features:

```powershell
python -m pytest examples --ezspec-report
```

Reports are written to `build/ezspec-report/` by default. Override the
destination when needed:

```powershell
python -m pytest examples --ezspec-report --ezspec-report-dir reports
```

Reporting can also be enabled and configured per feature:

```python
from ezspec import EzFeature, Feature
from ezspec.report import DisableEzSpecReport, EzFeatureReport


@EzFeature
@EzFeatureReport(formats=("txt", "json"), language="zh-TW")
class CheckoutSpec:
    feature = Feature.New("購物車結帳")


@EzFeature
@DisableEzSpecReport
class InternalOnlySpec:
    feature = Feature.New("不產生報告")
```

The JSON field names remain compatible with Java `ezspec-report`, including
scenario type discriminators and table raw data. The Python port supports TXT
and JSON reports only; the React dashboard is intentionally out of scope.

## Fluent scenario

Step callbacks are normal Python functions. They are registered while the
scenario is built and run later, in order, when `Execute()` is called.

```python
from ezspec import EzFeature, EzRule, EzScenario, Feature, ScenarioEnvironment


@EzFeature
class CheckoutSpec:
    feature = Feature.New("購物車結帳")

    @EzScenario
    def vip_customer_gets_discount(self) -> None:
        def prepare_cart(env: ScenarioEnvironment) -> None:
            env.put("price", 1000)

        def checkout(env: ScenarioEnvironment) -> None:
            env.put("total", env.geti("price") * 0.9)

        def verify_total(env: ScenarioEnvironment) -> None:
            assert env.get("total", float) == 900

        (
            self.feature.newScenario()
            .Given("購物車金額為 1000 元", prepare_cart)
            .When("VIP 顧客進行結帳", checkout)
            .Then("應付金額為 900 元", verify_total)
            .Execute()
        )
```

The pytest plugin collects `@EzFeature` classes and `@EzScenario` methods even
when their names do not start with `Test` or `test_`.

## Rules

All three ezSpec rule-selection styles are supported:

```python
scenario.withRule("VIP")


@EzScenario(rule="VIP")
def vip_scenario() -> None:
    feature.newScenario()


@EzRule("VIP")
class VipScenarios:
    @EzScenario
    def vip_scenario(self) -> None:
        feature.newScenario()
```

## Scenario Outline

```python
examples = """
| price | rate | total |
| 100   | 0.1  | 90    |
| 200   | 0.2  | 160   |
"""

(
    feature.newScenarioOutline("VIP discount")
    .WithExamples(examples)
    .Given("the price is <price>", prepare_price)
    .When("the discount rate is <rate>", apply_discount)
    .Then("the total is <total>", verify_total)
    .Execute()
)
```

## Execution behavior

- Steps share one `ScenarioEnvironment`.
- Fail-fast steps mark later steps as skipped.
- `ContinuousAfterFailure` aggregates multiple failures.
- `PendingException.pending()` marks a step pending.
- `ExecuteConcurrently()` runs each Given/When/Then concurrent group with a
  bounded thread pool.
- `DynamicExecute()` is preserved as a compatibility entry point; pytest owns
  dynamic test collection in Python.

The HTML dashboard from Java `ezspec-report` is not included in the Python port.
