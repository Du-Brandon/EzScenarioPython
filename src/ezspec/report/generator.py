"""Filesystem report generator for executed ezSpec feature classes."""

from __future__ import annotations

from collections.abc import Iterable
from os import PathLike
from pathlib import Path
from typing import Any

from ezspec.keyword import Feature

from .decorators import ReportConfig


DEFAULT_OUTPUT_DIR = Path("build/ezspec-report")
SUPPORTED_FORMATS = frozenset({"txt", "json"})


def _validated_formats(formats: Iterable[str]) -> tuple[str, ...]:
    values = (formats,) if isinstance(formats, str) else formats
    selected = tuple(dict.fromkeys(values))
    if not selected:
        raise ValueError("at least one report format is required")
    unsupported = [item for item in selected if item not in SUPPORTED_FORMATS]
    if unsupported:
        values = ", ".join(repr(item) for item in unsupported)
        raise ValueError(f"unsupported report format(s): {values}; use 'txt' or 'json'")
    return selected


def _qualified_name(owner: type[Any]) -> str:
    name = f"{owner.__module__}.{owner.__qualname__}"
    # Locally declared classes are useful in tests, but ``<`` and ``>`` are
    # invalid filename characters on Windows.
    return name.replace(".<locals>.", ".")


def _render_text(feature: Feature, *, language: str) -> str:
    from .plain_text import render_text

    return render_text(feature, language=language)


def _render_json(feature: Feature) -> str:
    from .json_report import render_json

    return render_json(feature)


def generate_feature_report(
    owner: type[Any],
    config: ReportConfig,
    *,
    output_dir: str | PathLike[str] | None = None,
) -> tuple[Path, ...]:
    """Generate the configured reports for ``owner.feature``.

    Missing or ``None`` feature fields are ignored, matching the Java report
    extension. A present field of the wrong type is treated as a configuration
    error so it cannot silently produce a misleading report.
    """

    feature = getattr(owner, "feature", None)
    if feature is None:
        return ()
    if not isinstance(feature, Feature):
        raise TypeError(f"{_qualified_name(owner)}.feature must be an ezspec Feature")

    formats = _validated_formats(config.formats)
    configured_destination = (
        output_dir if output_dir is not None else config.output_dir
    )
    destination = Path(configured_destination or DEFAULT_OUTPUT_DIR)
    destination.mkdir(parents=True, exist_ok=True)

    stem = _qualified_name(owner)
    generated: list[Path] = []
    for report_format in formats:
        path = destination / f"{stem}.{report_format}"
        if report_format == "txt":
            content = _render_text(feature, language=config.language)
        else:
            content = _render_json(feature)
        path.write_text(content, encoding="utf-8")
        generated.append(path)
    return tuple(generated)


generate_report = generate_feature_report

__all__ = [
    "DEFAULT_OUTPUT_DIR",
    "SUPPORTED_FORMATS",
    "generate_feature_report",
    "generate_report",
]
