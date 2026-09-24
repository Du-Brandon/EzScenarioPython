"""Scenario model and sequential/concurrent execution engine.

Adapted from ezSpec Scenario/RuntimeScenario, originally authored by Teddy Chen.
Modified for Python and concurrent step isolation; see NOTICE and
docs/SOURCE_PROVENANCE.md.
"""

from __future__ import annotations

import inspect
from concurrent.futures import ThreadPoolExecutor
from contextvars import ContextVar
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from ezspec.exception import EzSpecError, PendingException

from .environment import ScenarioEnvironment, _StepContext
from .registration import StepRegistrationMixin
from .result import Result
from .step import CONCURRENT_GROUP_STARTS, Step, StepCallback
from .table import Table

if TYPE_CHECKING:
    from .definition import OutlineDefinition
    from .rule import Background, Rule
    from .scenario_outline import ScenarioOutline


@dataclass
class _StepTable:
    value: Table
    changed: bool = False


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
        self._step_table: ContextVar[_StepTable | None] = ContextVar(
            "ezspec_active_step_table", default=None
        )

        if background is not None:
            self.runtime = ScenarioEnvironment.clone(background.getEnvironment())
            self.lookup_table = background.activeTable()
        else:
            self.lookup_table = table if table is not None else Table()
            self.runtime = ScenarioEnvironment.create().setInput(self.lookup_table)

        # Java field spelling is retained for integrations which inspect it.
        self.lookupTable = self.lookup_table

    @property
    def lookup_table(self) -> Table:
        state = self._step_table.get()
        return state.value if state is not None else self._lookup_table

    @lookup_table.setter
    def lookup_table(self, table: Table) -> None:
        state = self._step_table.get()
        if state is None:
            self._lookup_table = table
        else:
            state.value = table
            state.changed = True

    @property
    def lookupTable(self) -> Table:
        return self.lookup_table

    @lookupTable.setter
    def lookupTable(self, table: Table) -> None:
        self.lookup_table = table

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


class RuntimeScenario(Scenario, StepRegistrationMixin):
    """Stores step callbacks and executes them against one environment."""

    def __init__(
        self,
        name: str,
        rule: Rule | None = None,
        table: Table | None = None,
        background: Background | None = None,
        *,
        outline: ScenarioOutline | OutlineDefinition | None = None,
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

    def getScenarioOutline(self) -> ScenarioOutline | OutlineDefinition | None:
        return self.from_outline

    get_scenario_outline = getScenarioOutline

    def invokeStep(self, step: Step, description: str, callback: StepCallback) -> None:
        self.runtime.setArguments(Step.parseArguments(description))
        if Table.containsTable(description):
            self.lookup_table = Table(description)
            self.lookupTable = self.lookup_table
            self.runtime.setAnonymousTable(self.lookup_table)
        callback_result = callback(self.getEnvironment())
        if self.from_outline is not None:
            from .definition import OutlineDefinition

            if isinstance(self.from_outline, OutlineDefinition) and (
                inspect.isawaitable(callback_result)
                or inspect.isasyncgen(callback_result)
                or inspect.isgenerator(callback_result)
            ):
                if inspect.iscoroutine(callback_result) or inspect.isgenerator(
                    callback_result
                ):
                    callback_result.close()
                raise TypeError(
                    "OutlineDefinition callbacks must be synchronous and must not be generators"
                )
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

    def _execute_concurrent_step(
        self, step: Step, context: _StepContext, table: _StepTable
    ) -> None:
        token = self._step_table.set(table)
        try:
            with self.runtime._step_scope(context):
                self.executeStep(step)
        finally:
            self._step_table.reset(token)

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
            contexts = [self.runtime._capture_step_context() for _ in group]
            tables = [_StepTable(self.lookup_table) for _ in group]
            with ThreadPoolExecutor(max_workers=len(group)) as executor:
                futures = [
                    executor.submit(self._execute_concurrent_step, step, context, table)
                    for step, context, table in zip(group, contexts, tables, strict=True)
                ]
                for future in futures:
                    try:
                        future.result()
                    except BaseException:
                        # Results retain every failure; group policy is evaluated
                        # only after all callbacks in this group have completed.
                        pass

            self.runtime._merge_step_contexts(contexts)
            for table in tables:
                if table.changed:
                    self.lookup_table = table.value

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
