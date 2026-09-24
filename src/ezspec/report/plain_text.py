"""Plain-text renderer for an executed ezSpec feature tree.

Adapted from ezSpec's PlainTextReport.java. Original Java author: Teddy Chen.
Modified for Python rendering; see NOTICE and docs/SOURCE_PROVENANCE.md.
"""

from __future__ import annotations

from ezspec.keyword import (
    Background,
    Feature,
    Rule,
    RuntimeScenario,
    ScenarioOutline,
    Step,
    StepExecutionOutcome,
)

from .i18n import GherkinKeywords, get_gherkin_keywords


class PlainTextReport:
    """Collect a readable report while a feature dispatches visitor events."""

    def __init__(
        self,
        language: str | GherkinKeywords | None = "en",
    ) -> None:
        self._keywords = (
            language
            if isinstance(language, GherkinKeywords)
            else get_gherkin_keywords(language)
        )
        self._lines: list[str] = []

    def visit(self, element: object) -> None:
        """Render one specification element dispatched by ``Feature.accept``."""

        if isinstance(element, Feature):
            self._visit_feature(element)
        elif isinstance(element, Rule):
            self._visit_rule(element)
        elif isinstance(element, Background):
            self._visit_background(element)
        elif isinstance(element, ScenarioOutline):
            self._visit_scenario_outline(element)
        elif isinstance(element, RuntimeScenario):
            self._visit_runtime_scenario(element)
        elif isinstance(element, Step):
            self._visit_step(element)

    def _visit_feature(self, feature: Feature) -> None:
        lines = [f"{self._keyword(Feature.KEYWORD)}: {feature.getName()}"]
        lines.extend(self._description_lines(feature.getDescription()))
        self._append_block(lines)

    def _visit_rule(self, rule: Rule) -> None:
        lines = [f"{self._keyword(Rule.KEYWORD)}: {rule.getName()}"]
        lines.extend(self._description_lines(rule.description()))
        self._append_block(lines)

    def _visit_background(self, background: Background) -> None:
        if not background.steps():
            return
        name = background.getReplacedUnderscoresName()
        lines = [f"{self._keyword(Background.KEYWORD)}: {name}"]
        for step in background.steps():
            lines.append(self._step_definition(step))
        self._append_block(lines)

    def _visit_scenario_outline(self, outline: ScenarioOutline) -> None:
        keyword = self._keyword(ScenarioOutline.KEYWORD)
        lines = [f"{keyword}: {outline.getDisplayName()}", ""]
        description = self._description_lines(outline.getDescription())
        if description:
            lines.extend(description)
        lines.extend(self._step_definition(step) for step in outline.getSteps())

        for example in outline.getAllExamples():
            if lines and lines[-1] != "":
                lines.append("")
            example_keyword = self._keyword(example.KEYWORD)
            lines.append(f"{example_keyword}: {example.getName()}")
            lines.extend(self._description_lines(example.getDescription()))
            lines.extend(str(example.getTable()).rstrip("\n").splitlines())
        self._append_block(lines)

    def _visit_runtime_scenario(self, scenario: RuntimeScenario) -> None:
        if scenario.isFromScenarioOutline():
            label = scenario.activeTable().get("example_code")
            heading = f"[{scenario.getIndex() + 1}]"
            if label:
                heading += f" {label}"
            self._append_block([heading])
            return

        keyword = self._keyword(scenario.KEYWORD)
        name = scenario.getReplacedUnderscoresName()
        self._append_block([f"{keyword}: {name}"])

    def _visit_step(self, step: Step) -> None:
        result = step.getResult()
        line = f"[{result}] {self._keyword(step.getName())}"
        if step.description():
            line += f" {step.description()}"
        self._lines.append(line)

        outcome = result.getExecutionOutcome()
        message = result.getFailureMessage()
        if outcome is StepExecutionOutcome.Failure:
            self._lines.append(f"\t\t\tat {message}")
        elif outcome is StepExecutionOutcome.Pending and message:
            self._lines.append(f"\t\t\tcaused by {message}")

    def _step_definition(self, step: Step) -> str:
        line = self._keyword(step.getName())
        if step.description():
            line += f" {step.description()}"
        return line

    def _keyword(self, keyword: str) -> str:
        return self._keywords.getI18nKeyword(keyword)

    def getI18NKeyword(self, keyword: str) -> str:
        """Java-compatible spelling retained for report integrations."""

        return self._keyword(keyword)

    get_i18n_keyword = getI18NKeyword

    @staticmethod
    def _description_lines(description: str) -> list[str]:
        if not description:
            return []
        return description.strip("\n").splitlines()

    def _append_block(self, lines: list[str]) -> None:
        while lines and lines[-1] == "":
            lines.pop()
        if not lines:
            return
        if self._lines and self._lines[-1] != "":
            self._lines.append("")
        self._lines.extend(lines)

    def getOutput(self) -> str:
        return "\n".join(self._lines)

    get_output = getOutput


def render_text(
    feature: Feature,
    language: str | GherkinKeywords | None = "en",
) -> str:
    """Render ``feature`` without reading from or writing to the filesystem."""

    report = PlainTextReport(language)
    feature.accept(report)
    return report.getOutput()


__all__ = ["PlainTextReport", "render_text"]
