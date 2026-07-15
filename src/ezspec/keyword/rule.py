"""Feature rules and reusable scenario backgrounds."""

from __future__ import annotations

import inspect
from typing import TYPE_CHECKING

from .environment import ScenarioEnvironment
from .scenario import RuntimeScenario, Scenario

if TYPE_CHECKING:
    from .feature import Feature
    from .scenario_outline import ScenarioOutline


def _caller_name() -> str:
    frame = inspect.currentframe()
    try:
        # _caller_name -> Rule factory -> user test function
        caller = frame.f_back.f_back if frame and frame.f_back else None
        return caller.f_code.co_name if caller else "scenario"
    finally:
        del frame


class Background(RuntimeScenario):
    """A scenario whose environment is copied into scenarios in its rule."""

    KEYWORD = "Background"
    DEFAULT: "Background"

    def __init__(self, name: str, rule: "Rule | None") -> None:
        super().__init__(name=name, rule=rule)

    def withRule(self, rule_or_name: "Rule | str") -> "Background":
        old_rule = self.rule
        if old_rule is not None:
            old_rule.setBackground(Background.DEFAULT)
        super().withRule(rule_or_name)
        self.runtime = ScenarioEnvironment.create()
        self.rule.setBackground(self)
        return self

    with_rule = withRule

    def __str__(self) -> str:
        if not self.steps():
            return ""
        lines = [f"{self.KEYWORD}: {self.getReplacedUnderscoresName()}"]
        lines.extend(f"{step.getName()} {step.description()}".rstrip() for step in self.steps())
        return "\n".join(lines)


class Rule:
    """A business rule containing scenarios and at most one background."""

    KEYWORD = "Rule"

    def __init__(
        self,
        name: str,
        feature: "Feature | None",
        description: str = "",
        *,
        _background: Background | None = None,
    ) -> None:
        if name is None:
            raise TypeError("name cannot be None")
        self._name = name
        self._description = description
        self._scenarios: list[Scenario] = []
        self._feature = feature
        self._background = _background if _background is not None else Background.DEFAULT

    def description(self, value: str | None = None) -> str | "Rule":
        if value is None:
            return self._description
        self._description = value
        return self

    def newScenario(self, name: str | None = None) -> RuntimeScenario:
        scenario_name = _caller_name() if name is None else name
        for scenario in self._scenarios:
            if scenario.getName() == scenario_name:
                return scenario  # type: ignore[return-value]
        scenario = RuntimeScenario(
            name=scenario_name,
            rule=self,
            background=self._background,
        )
        self._scenarios.append(scenario)
        return scenario

    def newScenarioOutline(
        self, name: str | None = None, description: str = ""
    ) -> "ScenarioOutline":
        from .scenario_outline import ScenarioOutline

        outline_name = _caller_name() if name is None else name
        for scenario in self._scenarios:
            if scenario.getName() == outline_name:
                if not isinstance(scenario, ScenarioOutline):
                    raise TypeError(f"scenario named {outline_name!r} is not a ScenarioOutline")
                return scenario
        outline = ScenarioOutline(
            name=outline_name,
            description=description,
            background=self._background,
            rule=self,
        )
        self._scenarios.append(outline)
        return outline

    def newBackground(self, name: str | None = None) -> Background:
        self._background = Background(_caller_name() if name is None else name, self)
        return self._background

    def setBackground(self, background: Background) -> None:
        self._background = background

    def getScenarios(self) -> list[Scenario]:
        return self._scenarios

    def getName(self) -> str:
        return self._name

    def lastScenario(self) -> Scenario:
        return self._scenarios[-1]

    def lastScenarioOutline(self) -> "ScenarioOutline":
        from .scenario_outline import ScenarioOutline

        return next(
            scenario
            for scenario in reversed(self._scenarios)
            if isinstance(scenario, ScenarioOutline)
        )

    @staticmethod
    def Empty() -> "Rule":
        return Rule("Empty Rule", None, _background=Background.DEFAULT)

    def getBackground(self) -> Background:
        return self._background

    def getFeature(self) -> "Feature | None":
        return self._feature

    def accept(self, visitor: object) -> None:
        visit = getattr(visitor, "visit", None)
        if not callable(visit):
            raise TypeError("visitor must provide a callable visit method")
        if self._name:
            visit(self)
        self._background.accept(visitor)
        for scenario in self._scenarios:
            scenario.accept(visitor)

    def removeScenario(self, scenario: Scenario) -> None:
        self._scenarios[:] = [
            item for item in self._scenarios if item.getName() != scenario.getName()
        ]

    def addScenario(self, scenario: Scenario) -> None:
        if scenario not in self._scenarios:
            self._scenarios.append(scenario)

    new_scenario = newScenario
    new_scenario_outline = newScenarioOutline
    new_background = newBackground
    set_background = setBackground
    get_scenarios = getScenarios
    get_name = getName
    last_scenario = lastScenario
    last_scenario_outline = lastScenarioOutline
    empty = Empty
    get_background = getBackground
    get_feature = getFeature
    remove_scenario = removeScenario
    add_scenario = addScenario

    def __str__(self) -> str:
        lines: list[str] = []
        if self._name:
            lines.append(f"{self.KEYWORD}: {self._name}")
        if self._description:
            lines.append(self._description)
        if self._background is not Background.DEFAULT and str(self._background):
            lines.append(str(self._background))
        lines.extend(str(scenario).rstrip("\n") for scenario in self._scenarios)
        return "\n".join(lines) + ("\n" if lines else "")


# The sentinel intentionally has no owning rule or executable steps.
Background.DEFAULT = Background("", None)
