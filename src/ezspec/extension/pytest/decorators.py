"""pytest-compatible decorators mirroring ezSpec's JUnit 5 annotations.

Python adaptation of ezSpec's EzFeature and extension/junit5/Ez* annotations,
with pytest metadata and collection-time examples. See NOTICE and
docs/SOURCE_PROVENANCE.md for source and project attribution.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from functools import wraps
from typing import Any, TypeVar, overload

from ...runtime_context import rule_scope


F = TypeVar("F", bound=Callable[..., Any])
C = TypeVar("C", bound=type[Any])
_UNSET = object()


@dataclass(frozen=True, slots=True)
class OutlineConfig:
    """A declaration of collection-time data, separate from rule metadata."""

    examples: object


def get_outline_config(function: Any) -> OutlineConfig | None:
    return getattr(function, "__ezspec_outline_config__", None)


def _mark(target: F | C, kind: str, **metadata: str) -> F | C:
    setattr(target, "__ezspec_kind__", kind)
    kinds = set(getattr(target, "__ezspec_kinds__", ()))
    kinds.add(kind)
    setattr(target, "__ezspec_kinds__", frozenset(kinds))
    combined_metadata = dict(getattr(target, "__ezspec_metadata__", {}))
    combined_metadata.update(metadata)
    setattr(target, "__ezspec_metadata__", combined_metadata)
    return target


def EzFeature(cls: C) -> C:
    """Mark a class as an ezSpec feature container."""

    return _mark(cls, "feature")  # type: ignore[return-value]


@overload
def EzRule(cls: C, /) -> C: ...


@overload
def EzRule(value: str, /) -> Callable[[C], C]: ...


@overload
def EzRule(*, value: str = "") -> Callable[[C], C]: ...


def EzRule(
    cls: C | str | None = None,
    /,
    *,
    value: str = "",
) -> C | Callable[[C], C]:
    """Mark a class as an ezSpec rule container."""

    if isinstance(cls, str):
        if value:
            raise TypeError("rule value may be supplied positionally or by keyword, not both")
        value = cls
        cls = None

    def decorate(target: C) -> C:
        return _mark(target, "rule", value=value)  # type: ignore[return-value]

    return decorate if cls is None else decorate(cls)


def _scenario_decorator(
    kind: str,
    function: F | None,
    *,
    rule: str,
    examples: object = _UNSET,
) -> F | Callable[[F], F]:
    def decorate(target: F) -> F:
        @wraps(target)
        def wrapped(*args: Any, **kwargs: Any) -> Any:
            selected_rule = rule
            if not selected_rule and args:
                owner = type(args[0])
                owner_kinds = getattr(owner, "__ezspec_kinds__", ())
                if "rule" in owner_kinds:
                    selected_rule = getattr(owner, "__ezspec_metadata__", {}).get(
                        "value", ""
                    )
            with rule_scope(selected_rule):
                return target(*args, **kwargs)

        if examples is not _UNSET:
            wrapped.__ezspec_outline_config__ = OutlineConfig(examples)
        return _mark(wrapped, kind, rule=rule)  # type: ignore[return-value]

    return decorate if function is None else decorate(function)


@overload
def EzScenario(function: F, /) -> F: ...


@overload
def EzScenario(*, rule: str = "") -> Callable[[F], F]: ...


def EzScenario(
    function: F | None = None,
    /,
    *,
    rule: str = "",
) -> F | Callable[[F], F]:
    return _scenario_decorator("scenario", function, rule=rule)


@overload
def EzScenarioOutline(function: F, /) -> F: ...


@overload
def EzScenarioOutline(
    *, rule: str = "", examples: object = _UNSET
) -> Callable[[F], F]: ...


def EzScenarioOutline(
    function: F | None = None,
    /,
    *,
    rule: str = "",
    examples: object = _UNSET,
) -> F | Callable[[F], F]:
    return _scenario_decorator(
        "scenario_outline", function, rule=rule, examples=examples
    )


@overload
def EzDynamicScenario(function: F, /) -> F: ...


@overload
def EzDynamicScenario(*, rule: str = "") -> Callable[[F], F]: ...


def EzDynamicScenario(
    function: F | None = None,
    /,
    *,
    rule: str = "",
) -> F | Callable[[F], F]:
    return _scenario_decorator("dynamic_scenario", function, rule=rule)


@overload
def EzDynamicScenarioOutline(function: F, /) -> F: ...


@overload
def EzDynamicScenarioOutline(
    *, rule: str = "", examples: object = _UNSET
) -> Callable[[F], F]: ...


def EzDynamicScenarioOutline(
    function: F | None = None,
    /,
    *,
    rule: str = "",
    examples: object = _UNSET,
) -> F | Callable[[F], F]:
    return _scenario_decorator(
        "dynamic_scenario_outline", function, rule=rule, examples=examples
    )
