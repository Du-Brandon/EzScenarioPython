"""Serializable report DTOs compatible with the Java ezSpec JSON schema."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from ezspec.keyword import (
        Background,
        Example,
        Feature,
        Rule,
        RuntimeScenario,
        ScenarioOutline,
        Step,
    )
    from ezspec.keyword.table import Header, Row, Table


JsonDict = dict[str, object]


class SpecificationElementDto(Protocol):
    """Common serialization contract for scenarios and scenario outlines."""

    def to_dict(self) -> JsonDict: ...


@dataclass(frozen=True, slots=True)
class HeaderDto:
    header: tuple[str, ...]

    @classmethod
    def of(cls, header: "Header") -> "HeaderDto":
        return cls(tuple(header.header()))

    def to_dict(self) -> JsonDict:
        return {"header": list(self.header)}


@dataclass(frozen=True, slots=True)
class RowDto:
    columns: tuple[str, ...]

    @classmethod
    def of(cls, row: "Row") -> "RowDto":
        return cls(tuple(row.columns()))

    def to_dict(self) -> JsonDict:
        return {"columns": list(self.columns)}


@dataclass(frozen=True, slots=True)
class TableDto:
    headerDto: HeaderDto
    rows: tuple[RowDto, ...]
    RawData: str | None

    @classmethod
    def of(cls, table: "Table") -> "TableDto":
        return cls(
            headerDto=HeaderDto.of(table.header()),
            rows=tuple(RowDto.of(row) for row in table.rows()),
            RawData=table.getRawData(),
        )

    def to_dict(self) -> JsonDict:
        return {
            "headerDto": self.headerDto.to_dict(),
            "rows": [row.to_dict() for row in self.rows],
            "RawData": self.RawData,
        }


@dataclass(frozen=True, slots=True)
class ExampleDto:
    name: str
    description: str
    tableDto: TableDto

    @classmethod
    def of(cls, example: "Example") -> "ExampleDto":
        return cls(
            name=example.getName(),
            description=example.getDescription(),
            tableDto=TableDto.of(example.getTable()),
        )

    def to_dict(self) -> JsonDict:
        return {
            "name": self.name,
            "description": self.description,
            "tableDto": self.tableDto.to_dict(),
        }


def _exception_text(error: BaseException | None) -> str:
    if error is None:
        return ""
    exception_type = type(error)
    type_name = exception_type.__qualname__
    if exception_type.__module__ != "builtins":
        type_name = f"{exception_type.__module__}.{type_name}"
    message = str(error)
    return f"{type_name}: {message}" if message else type_name


@dataclass(frozen=True, slots=True)
class StepDto:
    keyword: str
    description: str
    stepExecutionOutcome: str
    errorMessage: str
    exception: str
    stackTrace: str
    continuousAfterFailure: bool

    @classmethod
    def of(cls, step: "Step") -> "StepDto":
        result = step.getResult()
        return cls(
            keyword=step.getName(),
            description=step.description(),
            stepExecutionOutcome=result.getExecutionOutcome().name,
            errorMessage=result.getFailureMessage(),
            exception=_exception_text(result.getException()),
            stackTrace=result.getStackTrace(),
            continuousAfterFailure=step.isContinuousAfterFailure(),
        )

    def to_dict(self) -> JsonDict:
        return {
            "keyword": self.keyword,
            "description": self.description,
            "stepExecutionOutcome": self.stepExecutionOutcome,
            "errorMessage": self.errorMessage,
            "exception": self.exception,
            "stackTrace": self.stackTrace,
            "continuousAfterFailure": self.continuousAfterFailure,
        }


@dataclass(frozen=True, slots=True)
class BackgroundDto:
    keyword: str
    name: str
    stepDtos: tuple[StepDto, ...]

    @classmethod
    def of(cls, background: "Background") -> "BackgroundDto":
        return cls(
            keyword=background.KEYWORD,
            name=background.getName(),
            stepDtos=tuple(StepDto.of(step) for step in background.steps()),
        )

    def to_dict(self) -> JsonDict:
        return {
            "keyword": self.keyword,
            "name": self.name,
            "stepDtos": [step.to_dict() for step in self.stepDtos],
        }


@dataclass(frozen=True, slots=True)
class ScenarioDto:
    keyword: str
    name: str
    stepDtos: tuple[StepDto, ...]

    @classmethod
    def of(cls, scenario: "RuntimeScenario") -> "ScenarioDto":
        return cls(
            keyword=scenario.KEYWORD,
            name=scenario.getName(),
            stepDtos=tuple(StepDto.of(step) for step in scenario.steps()),
        )

    def to_dict(self) -> JsonDict:
        return {
            "@class": "ScenarioDto",
            "keyword": self.keyword,
            "name": self.name,
            "stepDtos": [step.to_dict() for step in self.stepDtos],
        }


@dataclass(frozen=True, slots=True)
class ScenarioOutlineDto:
    keyword: str
    name: str
    rawStepDtos: tuple[StepDto, ...]
    allExampleDtos: tuple[ExampleDto, ...]
    runtimeScenarioDtos: tuple[ScenarioDto, ...]

    @classmethod
    def of(cls, outline: "ScenarioOutline") -> "ScenarioOutlineDto":
        return cls(
            keyword=outline.KEYWORD,
            name=outline.getName(),
            rawStepDtos=tuple(StepDto.of(step) for step in outline.getRawSteps()),
            allExampleDtos=tuple(
                ExampleDto.of(example) for example in outline.getAllExamples()
            ),
            runtimeScenarioDtos=tuple(
                ScenarioDto.of(scenario) for scenario in outline.RuntimeScenarios()
            ),
        )

    def to_dict(self) -> JsonDict:
        return {
            "@class": "ScenarioOutlineDto",
            "keyword": self.keyword,
            "name": self.name,
            "rawStepDtos": [step.to_dict() for step in self.rawStepDtos],
            "allExampleDtos": [example.to_dict() for example in self.allExampleDtos],
            "runtimeScenarioDtos": [
                scenario.to_dict() for scenario in self.runtimeScenarioDtos
            ],
        }


@dataclass(frozen=True, slots=True)
class RuleDto:
    keyword: str
    name: str
    description: str
    backgroundDto: BackgroundDto
    specificationElementDtos: tuple[SpecificationElementDto, ...]

    @classmethod
    def of(cls, rule: "Rule") -> "RuleDto":
        from ezspec.keyword import ScenarioOutline

        elements: list[SpecificationElementDto] = []
        for scenario in rule.getScenarios():
            if isinstance(scenario, ScenarioOutline):
                elements.append(ScenarioOutlineDto.of(scenario))
            else:
                elements.append(ScenarioDto.of(scenario))
        return cls(
            keyword=rule.KEYWORD,
            name=rule.getName(),
            description=rule.description(),
            backgroundDto=BackgroundDto.of(rule.getBackground()),
            specificationElementDtos=tuple(elements),
        )

    def to_dict(self) -> JsonDict:
        return {
            "keyword": self.keyword,
            "name": self.name,
            "description": self.description,
            "backgroundDto": self.backgroundDto.to_dict(),
            "specificationElementDtos": [
                element.to_dict() for element in self.specificationElementDtos
            ],
        }


@dataclass(frozen=True, slots=True)
class FeatureDto:
    keyword: str
    name: str
    description: str
    ruleDtos: tuple[RuleDto, ...]

    @classmethod
    def from_feature(cls, feature: "Feature") -> "FeatureDto":
        rules = (feature.getDefaultRule(), *feature.getRules())
        return cls(
            keyword=feature.KEYWORD,
            name=feature.getName(),
            description=feature.getDescription(),
            ruleDtos=tuple(RuleDto.of(rule) for rule in rules),
        )

    @classmethod
    def of(cls, feature: "Feature") -> "FeatureDto":
        return cls.from_feature(feature)

    def to_dict(self) -> JsonDict:
        return {
            "keyword": self.keyword,
            "name": self.name,
            "description": self.description,
            "ruleDtos": [rule.to_dict() for rule in self.ruleDtos],
        }
