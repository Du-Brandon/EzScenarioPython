"""Scenario Outline execution over one or more Examples tables.

Adapted from ezSpec's ScenarioOutline.java. Original Java author: Teddy Chen.
Modified for Python, including shared per-case construction;
see NOTICE and docs/SOURCE_PROVENANCE.md.
"""

from __future__ import annotations

import inspect
import re
from collections.abc import Iterable
from typing import TYPE_CHECKING, Any

from ezspec.exception import EzSpecError

from .examples import Example, Examples
from .scenario import RuntimeScenario
from .table import Table

if TYPE_CHECKING:
    from .rule import Background, Rule
    from .step import Step


def _caller_name() -> str:
    frame = inspect.currentframe()
    try:
        caller = frame.f_back.f_back if frame and frame.f_back else None
        return caller.f_code.co_name if caller else "scenario_outline"
    finally:
        del frame


def build_runtime_steps(raw_steps: Iterable["Step"], scenario: RuntimeScenario) -> None:
    """Copy template steps into a row with the legacy variable semantics."""
    table = scenario.activeTable()
    environment = scenario.getEnvironment()
    for raw_step in raw_steps:
        description = ScenarioOutline._replace_variables(raw_step.description(), table)
        for key in ScenarioOutline._variables(raw_step.description()):
            value = table.get(key)
            stored: object = Table(value) if Table.containsTable(value) else value
            environment.put(key, stored)

        method_name = {
            "Given": "Given",
            "When": "When",
            "Then": "Then",
            "And": "And",
            "But": "But",
            "Then success": "ThenSuccess",
            "Then failure": "ThenFailure",
        }.get(raw_step.getName())
        if method_name is None:
            raise RuntimeError(f"Unsupported step: {raw_step.getName()}")
        getattr(scenario, method_name)(
            description,
            raw_step.isContinuousAfterFailure(),
            raw_step.getCallback(),
        )


class ScenarioOutline(RuntimeScenario):
    """A scenario template executed once for every Examples row."""

    KEYWORD = "Scenario Outline"
    _VARIABLE = re.compile(r"<(.*?)>")

    def __init__(
        self,
        name: str,
        description: str,
        background: "Background",
        rule: "Rule",
    ) -> None:
        super().__init__(name=name, rule=rule, background=background)
        self._description = description
        self._all_examples: list[Example] = []
        self._runtime_scenarios: list[RuntimeScenario] = []

    @staticmethod
    def New(*args: Any) -> "ScenarioOutline":
        if len(args) == 1:
            rule = args[0]
            return rule.newScenarioOutline(_caller_name())
        if len(args) == 2:
            name, rule = args
            return rule.newScenarioOutline(name)
        if len(args) == 3:
            name, description, rule = args
            return rule.newScenarioOutline(name, description)
        raise TypeError("New expects rule, name/rule, or name/description/rule")

    new = New

    def getDescription(self) -> str:
        return self._description

    def getRawSteps(self) -> list["Step"]:
        return self.getSteps()

    def withRule(self, rule_or_name: "Rule | str") -> "ScenarioOutline":
        super().withRule(rule_or_name)
        return self

    with_rule = withRule

    def WithExamples(
        self,
        *values: str | Example | Examples | Iterable[Example],
    ) -> "ScenarioOutline":
        if not values:
            raise RuntimeError("require at least an example")
        if self._all_examples:
            return self

        expanded: list[str | Example | Examples] = []
        for value in values:
            if isinstance(value, (list, tuple)):
                expanded.extend(value)
            else:
                expanded.append(value)  # type: ignore[arg-type]

        if not expanded:
            raise RuntimeError("require at least an example")
        for value in expanded:
            if value is None:
                raise TypeError("example cannot be None")
            if isinstance(value, str):
                self._all_examples.append(Example(value))
            elif isinstance(value, Example):
                self._all_examples.append(value)
            elif isinstance(value, Examples):
                self._all_examples.append(value.getExample())
            else:
                raise TypeError(f"unsupported example type: {type(value).__name__}")
        self._build_runtime_scenarios()
        return self

    with_examples = WithExamples

    def _build_runtime_scenarios(self) -> None:
        self._runtime_scenarios.clear()
        runtime_index = 0
        for example in self._all_examples:
            for row_index in range(len(example.getTable().rows())):
                table = example.rowAsTable(row_index)
                scenario = RuntimeScenario(
                    name=self.getName(),
                    rule=self.rule,
                    table=table,
                    outline=self,
                    index=runtime_index,
                    background_runtime=self.runtime,
                )
                environment = scenario.getEnvironment()
                if hasattr(environment, "setExecutionCount"):
                    # Java ezSpec exposes a one-based execution count.
                    environment.setExecutionCount(runtime_index + 1)
                if hasattr(environment, "setInput"):
                    environment.setInput(table)
                self._runtime_scenarios.append(scenario)
                runtime_index += 1

    @classmethod
    def _variables(cls, description: str) -> list[str]:
        return cls._VARIABLE.findall(description)

    @classmethod
    def _replace_variables(cls, description: str, table: Table) -> str:
        for key in cls._variables(description):
            value = table.get(key)
            description = description.replace(f"<{key}>", f"<{value}>")
        return description

    def replaceScenarioOutlineVariables(
        self, description: str, table: Table | None = None
    ) -> str:
        active = table
        if active is None:
            if not self._runtime_scenarios:
                return description
            active = self._runtime_scenarios[0].activeTable()
        return self._replace_variables(description, active)

    replace_scenario_outline_variables = replaceScenarioOutlineVariables

    def _build_runtime_steps(self, scenario: RuntimeScenario) -> None:
        scenario.getSteps().clear()
        build_runtime_steps(self.getSteps(), scenario)

    def getAllExamples(self) -> tuple[Example, ...]:
        return tuple(self._all_examples)

    def RuntimeScenarios(self) -> tuple[RuntimeScenario, ...]:
        return tuple(self._runtime_scenarios)

    get_description = getDescription
    get_raw_steps = getRawSteps
    get_all_examples = getAllExamples
    runtime_scenarios = RuntimeScenarios

    def Execute(self) -> None:
        failures: list[BaseException] = []
        for scenario in self._runtime_scenarios:
            self._build_runtime_steps(scenario)
            try:
                scenario.Execute()
            except BaseException as error:
                failures.append(error)
        if failures:
            messages = "\n".join(f"[{i}] {error}" for i, error in enumerate(failures, 1))
            raise EzSpecError(failures, messages) from failures[0]

    execute = Execute

    def DynamicExecute(self) -> "ScenarioOutline":
        self.Execute()
        return self

    dynamic_execute = DynamicExecute

    def ExecuteConcurrently(self) -> None:
        failures: list[BaseException] = []
        for scenario in self._runtime_scenarios:
            self._build_runtime_steps(scenario)
            try:
                scenario.ExecuteConcurrently()
            except BaseException as error:
                failures.append(error)
        if failures:
            messages = "\n".join(f"[{i}] {error}" for i, error in enumerate(failures, 1))
            raise EzSpecError(failures, messages) from failures[0]

    execute_concurrently = ExecuteConcurrently

    def accept(self, visitor: object) -> None:
        visit = getattr(visitor, "visit", None)
        if not callable(visit):
            raise TypeError("visitor must provide a callable visit method")
        visit(self)
        for scenario in self._runtime_scenarios:
            scenario.accept(visitor)

    def __str__(self) -> str:
        text = f"{self.KEYWORD}: {self.getDisplayName()}\n\n"
        if self._description:
            text += f"{self._description}\n"
        for step in self.getSteps():
            text += step.getName()
            if step.description():
                text += f" {step.description()}"
            text += "\n"
        text += "".join(str(example) for example in self._all_examples)
        return text
