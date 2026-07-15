"""Class decorators that configure ezSpec report generation."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from os import PathLike
from pathlib import Path
from typing import Any, TypeVar, overload


C = TypeVar("C", bound=type[Any])

_REPORT_CONFIG_ATTRIBUTE = "__ezspec_report_config__"
_REPORT_DISABLED_ATTRIBUTE = "__ezspec_report_disabled__"


@dataclass(frozen=True, slots=True)
class ReportConfig:
    """Immutable per-feature report settings stored by ``EzFeatureReport``."""

    formats: tuple[str, ...] = ("txt", "json")
    language: str = "en"
    output_dir: Path | None = None


def _as_formats(formats: str | Iterable[str]) -> tuple[str, ...]:
    if isinstance(formats, str):
        return (formats,)
    return tuple(formats)


@overload
def EzFeatureReport(cls: C, /) -> C: ...


@overload
def EzFeatureReport(
    *,
    formats: str | Iterable[str] = ("txt", "json"),
    language: str = "en",
    output_dir: str | PathLike[str] | None = None,
) -> Callable[[C], C]: ...


def EzFeatureReport(
    cls: C | None = None,
    /,
    *,
    formats: str | Iterable[str] = ("txt", "json"),
    language: str = "en",
    output_dir: str | PathLike[str] | None = None,
) -> C | Callable[[C], C]:
    """Enable report generation for an ezSpec feature class.

    It supports both ``@EzFeatureReport`` and configured usage such as
    ``@EzFeatureReport(formats=("txt",), language="zh-TW")``.
    """

    config = ReportConfig(
        formats=_as_formats(formats),
        language=language,
        output_dir=Path(output_dir) if output_dir is not None else None,
    )

    def decorate(target: C) -> C:
        setattr(target, _REPORT_CONFIG_ATTRIBUTE, config)
        return target

    return decorate if cls is None else decorate(cls)


def DisableEzSpecReport(cls: C) -> C:
    """Disable report generation for a feature, including CLI-forced reports."""

    setattr(cls, _REPORT_DISABLED_ATTRIBUTE, True)
    return cls


def get_report_config(cls: type[Any]) -> ReportConfig | None:
    """Return report settings attached to ``cls``, if any."""

    value = getattr(cls, _REPORT_CONFIG_ATTRIBUTE, None)
    return value if isinstance(value, ReportConfig) else None


def is_report_disabled(cls: type[Any]) -> bool:
    """Return whether report generation is disabled for ``cls``."""

    return bool(getattr(cls, _REPORT_DISABLED_ATTRIBUTE, False))


__all__ = [
    "DisableEzSpecReport",
    "EzFeatureReport",
    "ReportConfig",
    "get_report_config",
    "is_report_disabled",
]
