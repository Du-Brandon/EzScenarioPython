from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from ezspec import EzFeature, Feature
from ezspec.extension.pytest import reporting
from ezspec.report.decorators import (
    DisableEzSpecReport,
    EzFeatureReport,
    ReportConfig,
    get_report_config,
)
from ezspec.report.generator import generate_feature_report


@EzFeature
@EzFeatureReport
class DecoratedFeature:
    feature = Feature.New("checkout")


@EzFeature
@DisableEzSpecReport
class DisabledFeature:
    feature = Feature.New("disabled")


@EzFeature
class CliFeature:
    feature = Feature.New("CLI")


class FakeConfig:
    def __init__(self, *, enabled: bool = False, output_dir: Path | None = None) -> None:
        self.stash: dict[object, Any] = {}
        self.options = {
            "ezspec_report": enabled,
            "ezspec_report_dir": str(output_dir) if output_dir is not None else None,
        }

    def getoption(self, name: str) -> Any:
        return self.options[name]


def test_report_decorator_supports_bare_and_configured_usage(tmp_path: Path) -> None:
    assert get_report_config(DecoratedFeature) == ReportConfig()

    @EzFeatureReport(formats="txt", language="zh-TW", output_dir=tmp_path)
    class ConfiguredFeature:
        pass

    assert get_report_config(ConfiguredFeature) == ReportConfig(
        formats=("txt",),
        language="zh-TW",
        output_dir=tmp_path,
    )


def test_generator_writes_utf8_reports_to_the_configured_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "ezspec.report.generator._render_text",
        lambda feature, *, language: f"{language}:{feature.getName()}",
    )
    monkeypatch.setattr(
        "ezspec.report.generator._render_json",
        lambda feature: f'{{"name":"{feature.getName()}"}}',
    )

    generated = generate_feature_report(
        DecoratedFeature,
        ReportConfig(language="zh-TW"),
        output_dir=tmp_path,
    )

    stem = f"{DecoratedFeature.__module__}.{DecoratedFeature.__qualname__}"
    assert generated == (tmp_path / f"{stem}.txt", tmp_path / f"{stem}.json")
    assert generated[0].read_text(encoding="utf-8") == "zh-TW:checkout"
    assert generated[1].read_text(encoding="utf-8") == '{"name":"checkout"}'


def test_generator_rejects_unknown_formats(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="use 'txt' or 'json'"):
        generate_feature_report(
            DecoratedFeature,
            ReportConfig(formats=("html",)),
            output_dir=tmp_path,
        )


def test_pytest_lifecycle_honors_decorator_cli_and_disable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = FakeConfig(enabled=True, output_dir=tmp_path)
    items = [
        SimpleNamespace(cls=DecoratedFeature),
        SimpleNamespace(cls=DecoratedFeature),
        SimpleNamespace(cls=CliFeature),
        SimpleNamespace(cls=DisabledFeature),
    ]
    generated: list[tuple[type[Any], ReportConfig, str | None]] = []

    def capture(
        owner: type[Any],
        report_config: ReportConfig,
        *,
        output_dir: str | None,
    ) -> tuple[Path, ...]:
        generated.append((owner, report_config, output_dir))
        return ()

    monkeypatch.setattr(reporting, "generate_feature_report", capture)
    reporting.pytest_collection_modifyitems(config, items)  # type: ignore[arg-type]
    session = SimpleNamespace(config=config)
    reporting.pytest_sessionfinish(session, 0)  # type: ignore[arg-type]

    assert generated == [
        (DecoratedFeature, ReportConfig(), str(tmp_path)),
        (CliFeature, ReportConfig(), str(tmp_path)),
    ]


def test_decorator_enables_reporting_without_cli(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = FakeConfig()
    generated: list[type[Any]] = []
    monkeypatch.setattr(
        reporting,
        "generate_feature_report",
        lambda owner, report_config, *, output_dir: generated.append(owner),
    )

    reporting.pytest_collection_modifyitems(
        config,  # type: ignore[arg-type]
        [SimpleNamespace(cls=DecoratedFeature)],
    )
    reporting.pytest_sessionfinish(
        SimpleNamespace(config=config),  # type: ignore[arg-type]
        0,
    )

    assert generated == [DecoratedFeature]
