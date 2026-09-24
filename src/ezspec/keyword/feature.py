"""Top-level Gherkin feature model.

Adapted from ezSpec's Feature.java. Original Java author: Teddy Chen.
Modified for Python, including declarative outlines;
see NOTICE and docs/SOURCE_PROVENANCE.md.
"""

from __future__ import annotations

import inspect

from ezspec.runtime_context import current_rule

from .definition import OutlineDefinition
from .rule import Background, Rule
from .scenario import Scenario
from .scenario_outline import ScenarioOutline


def _caller_name() -> str:
    frame = inspect.currentframe()
    try:
        caller = frame.f_back.f_back if frame and frame.f_back else None
        return caller.f_code.co_name if caller else "scenario"
    finally:
        del frame


class Feature:
    """A Gherkin feature containing a default rule and named rules."""

    KEYWORD = "Feature"

    def __init__(self, name: str, description: str = "") -> None:
        if name is None:
            raise TypeError("name cannot be None")
        if description is None:
            raise TypeError("description cannot be None")
        self._name = name
        self._description = description
        self._rules: list[Rule] = []
        self._default_rule = Rule("", self)

    @staticmethod
    def New(name: str, description: str = "") -> "Feature":
        return Feature(name, description)

    new = New

    def newBackground(self, name: str | None = None) -> Background:
        return self._default_rule.newBackground(_caller_name() if name is None else name)

    def getRule(self, rule_name: str) -> Rule | None:
        if rule_name is None:
            raise TypeError("rule name cannot be None")
        return next((rule for rule in self._rules if rule.getName() == rule_name), None)

    def applyRule(self, rule_name: str, scenario: Scenario) -> None:
        rule = self.getRule(rule_name)
        if rule is None:
            raise ValueError(f"Rule not found: {rule_name}")
        self._default_rule.removeScenario(scenario)
        if scenario.rule is not None and scenario.rule is not self._default_rule:
            scenario.rule.removeScenario(scenario)
        rule.addScenario(scenario)

    def initialize(self) -> None:
        self._rules.clear()
        self._default_rule = Rule("", self)

    def getRules(self) -> tuple[Rule, ...]:
        return tuple(self._rules)

    def getName(self) -> str:
        return self._name

    def getDescription(self) -> str:
        return self._description

    def newScenario(self, name: str | None = None) -> Scenario:
        scenario = self._default_rule.newScenario(_caller_name() if name is None else name)
        selected_rule = current_rule()
        return scenario.withRule(selected_rule) if selected_rule else scenario

    def newScenarioOutline(
        self, name: str | None = None, description: str = ""
    ) -> ScenarioOutline:
        outline = self._default_rule.newScenarioOutline(
            _caller_name() if name is None else name,
            description,
        )
        selected_rule = current_rule()
        return outline.withRule(selected_rule) if selected_rule else outline

    def defineScenarioOutline(
        self, name: str | None = None, description: str = ""
    ) -> OutlineDefinition:
        definition = OutlineDefinition(
            _caller_name() if name is None else name,
            description,
            self._default_rule,
        )
        selected_rule = current_rule()
        return definition.withRule(selected_rule) if selected_rule else definition

    def getDefaultRule(self) -> Rule:
        return self._default_rule

    def clearRule(self) -> None:
        self._rules.clear()

    def featureText(self) -> str:
        text = f"{self.KEYWORD}: {self._name}"
        if self._description:
            text += f"\n\n{self._description}"
        return text

    def accept(self, visitor: object) -> None:
        visit = getattr(visitor, "visit", None)
        if not callable(visit):
            raise TypeError("visitor must provide a callable visit method")
        visit(self)
        self._default_rule.accept(visitor)
        for rule in self._rules:
            rule.accept(visitor)

    def NewRule(self, rule_name: str, description: str = "") -> Rule:
        if rule_name is None:
            raise TypeError("rule name cannot be None")
        if any(rule.getName() == rule_name for rule in self._rules):
            raise ValueError(f"Rule name cannot be duplicated: {rule_name}")
        rule = Rule(rule_name, self, description)
        self._rules.append(rule)
        return rule

    new_background = newBackground
    get_rule = getRule
    apply_rule = applyRule
    get_rules = getRules
    get_name = getName
    get_description = getDescription
    new_scenario = newScenario
    new_scenario_outline = newScenarioOutline
    define_scenario_outline = defineScenarioOutline
    get_default_rule = getDefaultRule
    clear_rule = clearRule
    feature_text = featureText
    new_rule = NewRule

    def __str__(self) -> str:
        rule_text = str(self._default_rule)
        rule_text += "".join(str(rule) for rule in self._rules)
        return f"{self.featureText()}\n\n{rule_text}"
