"""A Scenario Outline template that can build one independent runtime row."""

from __future__ import annotations

import inspect
from typing import TYPE_CHECKING, Self

from .case import ExampleCase
from .registration import StepRegistrationMixin
from .scenario import RuntimeScenario, Scenario
from .scenario_outline import build_runtime_steps
from .step import Step, StepCallback

if TYPE_CHECKING:
    from .rule import Rule


class OutlineDefinition(StepRegistrationMixin):
    """Declarative steps and ownership, without execution or result state."""

    KEYWORD = "Scenario Outline"

    def __init__(self, name: str, description: str, rule: Rule) -> None:
        if name is None:
            raise TypeError("name must not be None")
        if description is None:
            raise TypeError("description must not be None")
        self._name = name
        self._description = description
        self.rule = rule
        self._steps: list[Step] = []

    def getName(self) -> str:
        return self._name

    get_name = getName

    def getDescription(self) -> str:
        return self._description

    get_description = getDescription

    def getDisplayName(self) -> str:
        return Scenario.replaceName(self._name)

    get_display_name = getDisplayName

    def steps(self) -> tuple[Step, ...]:
        return tuple(self._steps)

    def getSteps(self) -> tuple[Step, ...]:
        return self.steps()

    get_steps = getSteps

    def _append(
        self,
        step_type: type[Step],
        description: str,
        continuous_or_callback: bool | StepCallback,
        callback: StepCallback | None = None,
    ) -> Self:
        resolved = continuous_or_callback if callback is None else callback
        if (
            inspect.iscoroutinefunction(resolved)
            or inspect.isasyncgenfunction(resolved)
            or inspect.isgeneratorfunction(resolved)
        ):
            raise TypeError(
                "OutlineDefinition callbacks must be synchronous and must not be generators"
            )
        return super()._append(step_type, description, continuous_or_callback, callback)

    def withRule(self, rule_or_name: Rule | str) -> Self:
        if rule_or_name is None:
            raise TypeError("rule must not be None")
        feature = self.rule.getFeature()
        if feature is None:
            raise ValueError("scenario has no owning feature")
        rule_name = (
            rule_or_name if isinstance(rule_or_name, str) else rule_or_name.getName()
        )
        selected_rule = feature.getRule(rule_name)
        if selected_rule is None:
            raise ValueError(f"Rule not found: {rule_name}")
        self.rule = selected_rule
        return self

    with_rule = withRule

    def build_case(self, case: ExampleCase) -> RuntimeScenario:
        """Build a fresh executable scenario for exactly one examples row."""
        if not isinstance(case, ExampleCase):
            raise TypeError("case must be an ExampleCase")
        table = case.to_table()
        runtime = RuntimeScenario(
            self._name,
            rule=self.rule,
            table=table,
            outline=self,
            index=case.index,
            background_runtime=self.rule.getBackground().getEnvironment(),
        )
        build_runtime_steps(self._steps, runtime)
        return runtime
