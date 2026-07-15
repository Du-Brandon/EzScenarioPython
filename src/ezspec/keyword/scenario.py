"""Scenario model and sequential/concurrent execution engine."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import TYPE_CHECKING, Any

from ezspec.exception import EzSpecError, PendingException

from .environment import ScenarioEnvironment
from .result import Result
from .step import (
    CONCURRENT_GROUP_STARTS,
    And,
    But,
    Given,
    Step,
    StepCallback,
    Then,
    ThenFailure,
    ThenSuccess,
    When,
)
from .table import Table

if TYPE_CHECKING:
    from .rule import Background, Rule
    from .scenario_outline import ScenarioOutline


class Scenario:
    """Base representation shared by runtime scenarios and outlines."""

    KEYWORD = "Scenario"
    ARG = "$ARGUMENT"

    def __init__(
        self,
        name: str,
        rule: Rule | None = None,
        table: Table | None = None,
        background: Background | None = None,
    ) -> None:
        if name is None:
            raise TypeError("name must not be None")

        self.name = name
        self._steps: list[Step] = []
        self.rule = rule
        self.index = 0

        if background is not None:
            self.runtime = ScenarioEnvironment.clone(background.getEnvironment())
            self.lookup_table = background.activeTable()
        else:
            self.lookup_table = table if table is not None else Table()
            self.runtime = ScenarioEnvironment.create().setInput(self.lookup_table)

        # Java field spelling is retained for integrations which inspect it.
        self.lookupTable = self.lookup_table

    def getEnvironment(self) -> ScenarioEnvironment:
        return self.runtime

    get_environment = getEnvironment

    def activeTable(self) -> Table:
        return self.lookup_table

    active_table = activeTable

    def getName(self) -> str:
        return self.name

    get_name = getName

    @staticmethod
    def replaceName(origin_name: str) -> str:
        return (
            origin_name.replace("_", " ")
            .replace("$dot$", ".")
            .replace("$parenthesis$", "()")
            .replace("$comma$", ",")
        )

    replace_name = replaceName

    def getDisplayName(self) -> str:
        return self.replaceName(self.getName())

    get_display_name = getDisplayName

    def getReplacedUnderscoresName(self) -> str:
        return self.getName().replace("_", " ")

    get_replaced_underscores_name = getReplacedUnderscoresName

    def steps(self) -> tuple[Step, ...]:
        return tuple(self._steps)

    def getSteps(self) -> list[Step]:
        return self._steps

    get_steps = getSteps

    def withRule(self, rule_or_name: Rule | str) -> Scenario:
        if rule_or_name is None:
            raise TypeError("rule must not be None")
        if self.rule is None:
            raise ValueError("scenario has no owning feature")

        feature = self.rule.getFeature()
        if feature is None:
            raise ValueError("scenario has no owning feature")
        rule_name = (
            rule_or_name.getName() if not isinstance(rule_or_name, str) else rule_or_name
        )
        selected_rule = feature.getRule(rule_name)
        if selected_rule is None:
            raise ValueError(f"Rule not found: {rule_name}")

        feature.applyRule(rule_name, self)
        self.runtime = ScenarioEnvironment.clone(
            selected_rule.getBackground().getEnvironment()
        )
        self.rule = selected_rule
        return self

    with_rule = withRule

    def _buildSpecError(self, steps: list[Step] | tuple[Step, ...]) -> EzSpecError | None:
        messages = []
        for step in steps:
            if step.getResult().isFailure():
                messages.append(step.getResult().getFailureMessage())
        if not messages:
            return None
        return EzSpecError(
            "".join(
                f"\n[{index}] {message}"
                for index, message in enumerate(messages, 1)
            )
        )

    build_spec_error = _buildSpecError


class RuntimeScenario(Scenario):
    """Stores step callbacks and executes them against one environment."""

    def __init__(
        self,
        name: str,
        rule: Rule | None = None,
        table: Table | None = None,
        background: Background | None = None,
        *,
        outline: ScenarioOutline | None = None,
        index: int = 0,
        background_runtime: ScenarioEnvironment | None = None,
    ) -> None:
        super().__init__(name=name, rule=rule, table=table, background=background)
        self.from_outline = outline
        self.index = index

        if background_runtime is not None:
            combined = ScenarioEnvironment.clone(background_runtime)
            combined.addContext(self.runtime)
            self.runtime = combined

        if outline is not None:
            self.runtime.setExecutionCount(index + 1)

    def getIndex(self) -> int:
        return self.index

    get_index = getIndex

    def isFromScenarioOutline(self) -> bool:
        return self.from_outline is not None

    is_from_scenario_outline = isFromScenarioOutline

    def getScenarioOutline(self) -> ScenarioOutline | None:
        return self.from_outline

    get_scenario_outline = getScenarioOutline

    @staticmethod
    def _callback_args(
        continuous_or_callback: bool | StepCallback,
        callback: StepCallback | None,
    ) -> tuple[bool, StepCallback]:
        if callback is None and callable(continuous_or_callback):
            return Step.TerminateAfterFailure, continuous_or_callback
        if callback is None or not callable(callback):
            raise TypeError("callback must be callable")
        return bool(continuous_or_callback), callback

    def _append(
        self,
        step_type: type[Step],
        description: str,
        continuous_or_callback: bool | StepCallback,
        callback: StepCallback | None = None,
    ) -> RuntimeScenario:
        continuous, resolved_callback = self._callback_args(
            continuous_or_callback, callback
        )
        self._steps.append(step_type(description, continuous, resolved_callback))
        return self

    def Given(
        self,
        description: str,
        continuous_or_callback: bool | StepCallback,
        callback: StepCallback | None = None,
    ) -> RuntimeScenario:
        return self._append(Given, description, continuous_or_callback, callback)

    given = Given

    def When(
        self,
        description: str,
        continuous_or_callback: bool | StepCallback,
        callback: StepCallback | None = None,
    ) -> RuntimeScenario:
        return self._append(When, description, continuous_or_callback, callback)

    when = When

    def Then(
        self,
        description: str,
        continuous_or_callback: bool | StepCallback,
        callback: StepCallback | None = None,
    ) -> RuntimeScenario:
        return self._append(Then, description, continuous_or_callback, callback)

    then = Then

    def And(
        self,
        description: str,
        continuous_or_callback: bool | StepCallback,
        callback: StepCallback | None = None,
    ) -> RuntimeScenario:
        return self._append(And, description, continuous_or_callback, callback)

    and_ = And

    def But(
        self,
        description: str,
        continuous_or_callback: bool | StepCallback,
        callback: StepCallback | None = None,
    ) -> RuntimeScenario:
        return self._append(But, description, continuous_or_callback, callback)

    but = But

    @staticmethod
    def _then_special_args(args: tuple[Any, ...]) -> tuple[str, bool, StepCallback]:
        description = ""
        continuous = Step.TerminateAfterFailure
        callback: StepCallback | None = None

        if len(args) == 1 and callable(args[0]):
            callback = args[0]
        elif len(args) == 2 and isinstance(args[0], bool) and callable(args[1]):
            continuous, callback = args
        elif len(args) == 2 and isinstance(args[0], str) and callable(args[1]):
            description, callback = args
        elif (
            len(args) == 3
            and isinstance(args[0], str)
            and isinstance(args[1], bool)
            and callable(args[2])
        ):
            description, continuous, callback = args
        else:
            raise TypeError(
                "expected callback, bool/callback, description/callback, "
                "or description/bool/callback"
            )
        return description, continuous, callback

    def ThenSuccess(self, *args: Any) -> RuntimeScenario:
        description, continuous, callback = self._then_special_args(args)
        return self._append(ThenSuccess, description, continuous, callback)

    then_success = ThenSuccess

    def ThenFailure(self, *args: Any) -> RuntimeScenario:
        description, continuous, callback = self._then_special_args(args)
        return self._append(ThenFailure, description, continuous, callback)

    then_failure = ThenFailure

    def invokeStep(self, step: Step, description: str, callback: StepCallback) -> None:
        self.runtime.setArguments(Step.parseArguments(description))
        if Table.containsTable(description):
            self.lookup_table = Table(description)
            self.lookupTable = self.lookup_table
            self.runtime.setAnonymousTable(self.lookup_table)
        callback(self.getEnvironment())
        step.setResult(Result.Success())

    invoke_step = invokeStep

    def executeStep(self, step: Step) -> None:
        try:
            self.invokeStep(step, step.description(), step.getCallback())
        except PendingException as error:
            step.setResult(Result.Pending(error))
        except BaseException as error:
            step.setResult(Result.Failure(error))
            raise

    execute_step = executeStep

    def doExecute(self, throw_exception: bool) -> None:
        for index, step in enumerate(self._steps):
            try:
                self.executeStep(step)
            except BaseException:
                if not step.isContinuousAfterFailure():
                    self._skip_from(index + 1)
                    if throw_exception:
                        raise
                    break

    do_execute = doExecute

    def preExecuteScenario(self) -> None:
        self.doExecute(False)

    pre_execute_scenario = preExecuteScenario

    def Execute(self) -> None:
        self.doExecute(True)
        spec_error = self._buildSpecError(self._steps)
        if spec_error is not None:
            raise spec_error

    execute = Execute

    def DynamicExecute(self) -> RuntimeScenario:
        """Execute through pytest and return this scenario for inspection.

        JUnit's ``DynamicNode`` has no direct pytest equivalent.  The Python
        port preserves the fluent entry point while pytest handles collection.
        """

        self.Execute()
        return self

    dynamic_execute = DynamicExecute

    def doExecuteConcurrently(self) -> int:
        if self._steps and not isinstance(self._steps[0], CONCURRENT_GROUP_STARTS):
            raise RuntimeError(
                "A concurrent scenario must start with a Given, When, or Then"
            )

        current = 0
        while current < len(self._steps):
            next_group = current + 1
            while next_group < len(self._steps) and not isinstance(
                self._steps[next_group], CONCURRENT_GROUP_STARTS
            ):
                next_group += 1

            group = self._steps[current:next_group]
            with ThreadPoolExecutor(max_workers=len(group)) as executor:
                futures = [executor.submit(self.executeStep, step) for step in group]
                for future in futures:
                    try:
                        future.result()
                    except BaseException:
                        # Results retain every failure; group policy is evaluated
                        # only after all callbacks in this group have completed.
                        pass

            current = next_group
            if any(
                step.getResult().isFailure()
                and not step.isContinuousAfterFailure()
                for step in group
            ):
                self._skip_from(current)
                break
        return current

    do_execute_concurrently = doExecuteConcurrently

    def ExecuteConcurrently(self) -> None:
        executed_end = self.doExecuteConcurrently()
        spec_error = self._buildSpecError(self._steps[:executed_end])
        if spec_error is not None:
            raise spec_error

    execute_concurrently = ExecuteConcurrently

    def _skip_from(self, start: int) -> None:
        for step in self._steps[start:]:
            step.setResult(Result.Skip())

    def accept(self, visitor: Any) -> None:
        if str(self):
            visitor.visit(self)
        for step in self._steps:
            if hasattr(step, "accept"):
                step.accept(visitor)
            else:
                visitor.visit(step)

    def __str__(self) -> str:
        lines = [f"{self.KEYWORD}: {self.replaceName(self.getName())}"]
        for step in self._steps:
            line = step.getName()
            if step.description():
                line += " " + Step.eraseReservedWords(step.description())
            lines.append(line)
        return "\n".join(lines) + "\n"
