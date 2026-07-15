"""Runtime state shared by all steps in a scenario."""

from __future__ import annotations

from typing import Any, Iterable

from .argument import Argument
from .table import Row, Table


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

    def __init__(self) -> None:
        self.execution_count = 0
        self._context: dict[str, Any] = {
            self.ARGUMENTS_KEY: [],
            self.HISTORICAL_ARGUMENTS_KEY: [],
        }

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
        if env.ANONYMOUS_TABLE_KEY in env._context:
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
        self._context.update(runtime._context)

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
        self._context[key] = value
        return self

    def get(self, key: str, cls: type[Any] | None = None) -> Any:
        # Java's Class argument only controls its generic cast.  Deliberately do
        # not coerce here; callers receive the same object that was put in.
        return self._context.get(key)

    def gets(self, key: str) -> str:
        value = self._context.get(key, "")
        return value if isinstance(value, str) else str(value)

    def geti(self, key: str) -> int:
        return int(self.gets(key).replace(",", ""))

    def gett(self, key: str) -> Table | None:
        return self.get(key, Table)

    def getArgs(self) -> tuple[Argument, ...]:
        return tuple(self._arguments())

    get_args = getArgs

    def getHistoricalArgs(self) -> tuple[Argument, ...]:
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
        if isinstance(index_or_key, int):
            return self._argument_value(self._historical_arguments()[index_or_key])

        for argument in self._historical_arguments():
            if self._argument_key(argument) == index_or_key:
                return self._argument_value(argument)
        raise LookupError(f"Historical argument not found: {index_or_key}")

    get_historical_arg = getHistoricalArg

    def setArguments(self, arguments: Iterable[Argument]) -> None:
        current = self._arguments()
        current.clear()
        current.extend(arguments)
        self._historical_arguments().extend(current)

    set_arguments = setArguments

    def _arguments(self) -> list[Argument]:
        return self._context[self.ARGUMENTS_KEY]

    def _historical_arguments(self) -> list[Argument]:
        return self._context[self.HISTORICAL_ARGUMENTS_KEY]

    def _require_anonymous_table(self) -> None:
        if self.ANONYMOUS_TABLE_KEY not in self._context:
            raise RuntimeError("No anonymous table in the scenario.")

    @staticmethod
    def _argument_key(argument: Argument) -> str:
        key = argument.key
        return key() if callable(key) else key

    @staticmethod
    def _argument_value(argument: Argument) -> str:
        value = argument.value
        return value() if callable(value) else value
