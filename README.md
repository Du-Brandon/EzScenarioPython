# EzScenarioPython

EzScenarioPython is an independently maintained Python port of
[ezSpec](https://gitlab.com/TeddyChen/ezspec)'s developer-facing BDD internal DSL.
It keeps the original Feature, Rule, Scenario, Given, When, Then, and Execute
vocabulary while integrating with pytest.

The Java reference source is pinned to
[commit `061eadc8`](https://gitlab.com/TeddyChen/ezspec/-/tree/061eadc8dd47510bf12d62dd87d3fdaa0a37b20d).
Its root `pom.xml` declares revision `2.0.5`; the commit identifies the reference
precisely. The Java checkout is not needed to run this Python project.

**Status: experimental.** APIs may change before a stable release. Source code,
examples, and issue tracking are the initial GitHub distribution; install from
a local checkout using the instructions below. See [known limitations](#known-limitations)
before relying on test results.

## Requirements

- Python 3.11 or newer
- pytest 8 or newer (declared development dependency)

Validated on Windows with Python 3.11.2: all 199 tests pass with both pytest 8.3.3 and 9.1.1.

## Install from source

Clone this repository or download its source archive, open a terminal in the
project directory, and create a virtual environment:

```powershell
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
```

On Linux or macOS, activate it with `source .venv/bin/activate`. Then install
the project together with pytest and run its specifications:

```powershell
python -m pip install -e ".[dev]"
python -m pytest
```

The `dev` extra currently supplies pytest, which is required for the runner
integration. To contribute, see [CONTRIBUTING.md](CONTRIBUTING.md).

## Executable samples

The Java `ezspec-sample` module is represented by executable specifications
under `examples/`. Run them independently with:

```powershell
python -m pytest examples -q
```

They cover Scenario and Scenario Outline usage with both the default Rule and
named Rules. The outline samples demonstrate raw tables, reusable
`PytestExamples`, lists of examples, and nested tables. Their Examples sources
are available during pytest collection, so each row becomes a separate item.

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

Inspect the collected rows before running them:

```powershell
python -m pytest examples --collect-only -q
```

pytest displays a separate node id for every Outline row. Copy a complete
node id from the collection output to rerun exactly that row:

```powershell
python -m pytest 'examples/default_rule/test_scenario_outline_example.py::ScenarioOutlineExample::scenario_outline_example_with_table_input[e1-r2]' -q
```

The bracketed ID is generated from the Examples group and row when there is
no unique `example_code` column. Use the exact ID shown by `--collect-only`
for your data. Add `--ezspec-steps` to show each row's Given, When, Then and
their results in the terminal:

```powershell
python -m pytest examples --ezspec-steps
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

Reports are written to `build/ezspec-report/` by default. The TXT and Java
schema compatible JSON show the specification; each feature's
`.execution.json` records which Outline rows were collected, selected, and
run, together with their pytest phase results. This makes partial reruns
distinguishable from a full Examples run. TXT reports identify each Outline's
Rule, source method, and additional pytest parameters. Fixture errors remain
visible even for a header-only, zero-row Outline. Override the destination when needed:

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

For one pytest item per Examples row, declare a source that is available at
collection time and pass it to the decorator. The method returns a definition;
pytest executes the selected row after fixture setup:

```python
from ezspec import EzFeature, EzScenarioOutline, Feature

VIP_DISCOUNTS = """
| price | rate | total |
| 100   | 0.1  | 90    |
| 200   | 0.2  | 160   |
"""


def prepare_price(env):
    env.put("price", env.geti("price"))


def apply_discount(env):
    env.put("actual", env.geti("price") * (1 - float(env.gets("rate"))))


def verify_total(env):
    assert env.get("actual") == env.geti("total")


@EzFeature
class DiscountSpec:
    feature = Feature.New("Discounts")

    @EzScenarioOutline(examples=VIP_DISCOUNTS)
    def vip_discount(self):
        return (
            self.feature.defineScenarioOutline("VIP discount")
            .Given("the price is <price>", prepare_price)
            .When("the discount rate is <rate>", apply_discount)
            .Then("the total is <total>", verify_total)
        )
```

An Examples source may also be a `PytestExamples.get(...)` value or a list
or tuple of sources. Construct lists before collection, for example at module
scope. A named Rule can be selected with `rule="VIP"` in the decorator and
`.withRule(...)` on the definition.

The existing `newScenarioOutline().WithExamples(...).Execute()` style remains
available as one pytest item. Omitting `WithExamples` there keeps Java's
no-op behavior. An explicit empty Examples list raises a parameter error in
either style. A table with a header but no data rows produces one
`[no-examples]` placeholder item without running scenario callbacks. Use the
decorator form when individual rows need collection and rerun.

Callbacks in the decorator form must execute synchronously. Coroutine and
generator callbacks, including wrapped callbacks that return these objects,
raise an error instead of reporting success without executing their assertions.
pytest fixtures can still use `yield` for setup and teardown.

## Execution behavior

- Steps share one `ScenarioEnvironment`.
- Fail-fast steps mark later steps as skipped.
- `ContinuousAfterFailure` aggregates multiple failures.
- `PendingException.pending()` marks a step pending.
- `ExecuteConcurrently()` runs each Given/When/Then concurrent group with a
  bounded thread pool. Active arguments and anonymous-table assignments are
  isolated per step; normal user values remain shared across the scenario.
- `DynamicExecute()` is preserved as a compatibility entry point; pytest owns
  dynamic test collection in Python.

The HTML dashboard from Java `ezspec-report` is not included in the Python port.

Concurrent groups wait for all their callbacks before the next group starts.
A step without its own table inherits the table available before its group.
After a group finishes, the last explicitly assigned table in declaration order
is available to later groups. Argument history retains every invocation, but
ordering within a concurrent group depends on scheduling. Shared user objects
and inherited tables are shallow references; synchronize compound updates and
in-place mutations yourself. See [concurrent execution](docs/CONCURRENT_EXECUTION.md)
for the execution contract.

## Known limitations

- A Pending step is recorded as Pending but does not by itself make pytest skip
  or fail the test. Review step results when checking specification completeness.
- An Outline without Examples keeps Java's no-op behavior. A passing pytest
  item can therefore mean no data rows were validated; reports show zero rows.
- Row-wise reporting does not yet merge results from pytest-xdist workers.
- The new Outline API supports synchronous callbacks only. IDE presentation
  depends on its pytest integration; steps are not separate pytest items.
- Local validation covers Windows / Python 3.11.2 with pytest 8.3.3 and 9.1.1.
  The GitHub workflow also defines Linux and Python 3.12/3.13 checks; those
  environments remain unverified until CI has run successfully.

## License and contributions

Distributed under [Apache-2.0](LICENSE). See [NOTICE](NOTICE) for ezSpec source
attribution and [source provenance](docs/SOURCE_PROVENANCE.md) for the
reference-file mapping and scope of the Python adaptation. Contributions should retain
applicable upstream notices and identify changes to adapted files.

Read [CONTRIBUTING.md](CONTRIBUTING.md) for development and pull requests,
[SECURITY.md](SECURITY.md) for vulnerability reporting, and
[CHANGELOG.md](CHANGELOG.md) for changes.
