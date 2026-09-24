"""Shared scenario values with isolated inputs for concurrent steps.

Adapted from ezSpec ScenarioEnvironment, originally authored by Teddy Chen.
Modified for Python and concurrent step isolation; see NOTICE and
docs/SOURCE_PROVENANCE.md.
"""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from threading import RLock
from typing import Any, Iterable, Iterator

from .argument import Argument
from .table import Row, Table


@dataclass
class _StepContext:
    values: dict[str, Any]
    changed: set[str] = field(default_factory=set)


class ScenarioEnvironment:
    """Carries arguments, tables, and user values between scenario steps.

    Cloning intentionally performs a shallow copy of user values.  This mirrors
    ezSpec's Java implementation and allows a background to provide domain
    objects which are then reused by its scenario.
    """

    INPUT_KEY = "$INPUT"
    ANONYMOUS_TABLE_KEY = "$ANONYMOUS_TABLE"
    ARGUMENTS_KEY = "$ARGUMENTS"
    HISTORICAL_ARGUMENTS_KEY = "$HISTORICAL_ARGUMENTS"
    _STEP_KEYS = frozenset({ARGUMENTS_KEY, ANONYMOUS_TABLE_KEY})

    def __init__(self) -> None:
        self.execution_count = 0
        self._context: dict[str, Any] = {
            self.ARGUMENTS_KEY: [],
            self.HISTORICAL_ARGUMENTS_KEY: [],
        }
        self._step_context: ContextVar[_StepContext | None] = ContextVar(
            "ezspec_step_context", default=None
        )
        self._history_lock = RLock()

    def _capture_step_context(self) -> _StepContext:
        """Snapshot a group's inputs before any of its workers can modify them."""

        values: dict[str, Any] = {self.ARGUMENTS_KEY: list(self.getArgs())}
        source = self._value_context(self.ANONYMOUS_TABLE_KEY)
        if self.ANONYMOUS_TABLE_KEY in source:
            values[self.ANONYMOUS_TABLE_KEY] = source[self.ANONYMOUS_TABLE_KEY]
        return _StepContext(values)

    @contextmanager
    def _step_scope(self, state: _StepContext) -> Iterator[None]:
        token = self._step_context.set(state)
        try:
            yield
        finally:
            self._step_context.reset(token)

    def _merge_step_contexts(self, states: Iterable[_StepContext]) -> None:
        """Commit completed inputs in declaration order after the group barrier.

        History was recorded at invocation time and must not be appended again.
        A nested group commits to its enclosing step's context.
        """

        for state in states:
            for key in state.changed:
                self.put(key, state.values[key])

    def _value_context(self, key: str) -> dict[str, Any]:
        state = self._step_context.get()
        if state is not None and key in self._STEP_KEYS:
            return state.values
        return self._context

    @classmethod
    def create(cls) -> ScenarioEnvironment:
        return cls()

    @classmethod
    def clone(cls, env: ScenarioEnvironment) -> ScenarioEnvironment:
        if env is None:
            raise TypeError("env must not be None")

        cloned = cls.create()
        cloned._historical_arguments().extend(env.getHistoricalArgs())

        if env.INPUT_KEY in env._context:
            cloned.put(cls.INPUT_KEY, env.getInput())
        if env.ANONYMOUS_TABLE_KEY in env._value_context(env.ANONYMOUS_TABLE_KEY):
            cloned.setAnonymousTable(env.get(cls.ANONYMOUS_TABLE_KEY, Table))

        reserved = {
            cls.INPUT_KEY,
            cls.ANONYMOUS_TABLE_KEY,
            cls.ARGUMENTS_KEY,
            cls.HISTORICAL_ARGUMENTS_KEY,
        }
        for key, value in env._context.items():
            if key not in reserved:
                cloned._context[key] = value
        return cloned

    def setInput(self, table: Table) -> ScenarioEnvironment:
        return self.put(self.INPUT_KEY, table)

    set_input = setInput

    def getInput(self) -> Table | None:
        return self.get(self.INPUT_KEY, Table)

    get_input = getInput

    def getExecutionCount(self) -> int:
        return self.execution_count

    get_execution_count = getExecutionCount

    def setExecutionCount(self, execution_count: int) -> None:
        self.execution_count = execution_count

    set_execution_count = setExecutionCount

    def addContext(self, runtime: ScenarioEnvironment) -> None:
        values = dict(runtime._context)
        state = runtime._step_context.get()
        if state is not None:
            for key in self._STEP_KEYS:
                if key in state.values:
                    values[key] = state.values[key]
                else:
                    values.pop(key, None)
        for key, value in values.items():
            self.put(key, value)

    add_context = addContext

    def setAnonymousTable(self, table: Table) -> ScenarioEnvironment:
        return self.put(self.ANONYMOUS_TABLE_KEY, table)

    set_anonymous_table = setAnonymousTable

    def table(self) -> Table:
        self._require_anonymous_table()
        return self.get(self.ANONYMOUS_TABLE_KEY, Table)

    def lastRow(self) -> Row:
        return self.table().lastRow()

    last_row = lastRow

    def row(self, index_or_first_column: int | str) -> Row:
        return self.table().row(index_or_first_column)

    def put(self, key: str, value: Any) -> ScenarioEnvironment:
        state = self._step_context.get()
        if state is not None and key in self._STEP_KEYS:
            state.values[key] = value
            state.changed.add(key)
        else:
            self._context[key] = value
        return self

    def get(self, key: str, cls: type[Any] | None = None) -> Any:
        # Java's Class argument only controls its generic cast.  Deliberately do
        # not coerce here; callers receive the same object that was put in.
        return self._value_context(key).get(key)

    def gets(self, key: str) -> str:
        value = self._value_context(key).get(key, "")
        return value if isinstance(value, str) else str(value)

    def geti(self, key: str) -> int:
        return int(self.gets(key).replace(",", ""))

    def gett(self, key: str) -> Table | None:
        return self.get(key, Table)

    def getArgs(self) -> tuple[Argument, ...]:
        return tuple(self._arguments())

    get_args = getArgs

    def getHistoricalArgs(self) -> tuple[Argument, ...]:
        with self._history_lock:
            return tuple(self._historical_arguments())

    get_historical_args = getHistoricalArgs

    def hasArgument(self) -> bool:
        return bool(self._arguments())

    has_argument = hasArgument

    def getArg(self, index_or_key: int | str) -> str:
        if isinstance(index_or_key, int):
            return self._argument_value(self._arguments()[index_or_key])

        for argument in self._arguments():
            if self._argument_key(argument) == index_or_key:
                return self._argument_value(argument)
        raise LookupError(f"Argument not found: {index_or_key}")

    get_arg = getArg

    def getArgi(self, index_or_key: int | str) -> int:
        return int(self.getArg(index_or_key).replace(",", ""))

    get_argi = getArgi

    def getArgd(self, index_or_key: int | str) -> float:
        value = self.getArg(index_or_key)
        if value.endswith("%"):
            return float(value[:-1].replace(",", "")) / 100.0
        return float(value.replace(",", ""))

    get_argd = getArgd

    def getHistoricalArg(self, index_or_key: int | str) -> str:
        historical = self.getHistoricalArgs()
        if isinstance(index_or_key, int):
            return self._argument_value(historical[index_or_key])

        for argument in historical:
            if self._argument_key(argument) == index_or_key:
                return self._argument_value(argument)
        raise LookupError(f"Historical argument not found: {index_or_key}")

    get_historical_arg = getHistoricalArg

    def setArguments(self, arguments: Iterable[Argument]) -> None:
        values = list(arguments)
        current = self._arguments()
        current.clear()
        current.extend(values)
        state = self._step_context.get()
        if state is not None:
            state.changed.add(self.ARGUMENTS_KEY)
        with self._history_lock:
            self._historical_arguments().extend(values)

    set_arguments = setArguments

    def _arguments(self) -> list[Argument]:
        return self._value_context(self.ARGUMENTS_KEY)[self.ARGUMENTS_KEY]

    def _historical_arguments(self) -> list[Argument]:
        return self._context[self.HISTORICAL_ARGUMENTS_KEY]

    def _require_anonymous_table(self) -> None:
        if self.ANONYMOUS_TABLE_KEY not in self._value_context(self.ANONYMOUS_TABLE_KEY):
            raise RuntimeError("No anonymous table in the scenario.")

    @staticmethod
    def _argument_key(argument: Argument) -> str:
        key = argument.key
        return key() if callable(key) else key

    @staticmethod
    def _argument_value(argument: Argument) -> str:
        value = argument.value
        return value() if callable(value) else value
