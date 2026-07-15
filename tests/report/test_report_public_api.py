from ezspec.report import (
    DisableEzSpecReport,
    EzFeatureReport,
    FeatureDto,
    PlainTextReport,
    ReportConfig,
    generate_feature_report,
    render_json,
    render_text,
)
from ezspec.pytest_plugin import pytest_addoption, pytest_sessionfinish


def test_report_package_exposes_the_supported_mvp_api() -> None:
    assert callable(EzFeatureReport)
    assert callable(DisableEzSpecReport)
    assert callable(generate_feature_report)
    assert callable(render_json)
    assert callable(render_text)
    assert FeatureDto.__name__ == "FeatureDto"
    assert PlainTextReport.__name__ == "PlainTextReport"
    assert ReportConfig().formats == ("txt", "json")
    assert callable(pytest_addoption)
    assert callable(pytest_sessionfinish)
