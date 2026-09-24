"""Exercise collection, fixtures, selection, and failures in real pytest runs."""

from __future__ import annotations

import os
import json
from pathlib import Path
import subprocess
import sys
import textwrap

import pytest


_SOURCE = Path(__file__).resolve().parents[1] / "src"
_CASES = "| example_code | value |\n| A | 10 |\n| B | 20 |\n| C | 30 |"


@pytest.fixture
def spec_runner(tmp_path):
    """Keep subprocess artifacts for diagnosis and never install packages."""

    (tmp_path / "pytest.ini").write_text(
        "[pytest]\nmarkers =\n"
        "    ezfeature: feature\n    ezscenario: scenario\n"
        "    ezscenario_outline: outline\n",
        encoding="utf-8",
    )

    def run(source, *arguments):
        (tmp_path / "test_spec.py").write_text(textwrap.dedent(source), encoding="utf-8")
        environment = dict(os.environ)
        environment.update(
            PYTHONPATH=os.pathsep.join(
                part for part in (str(_SOURCE), os.environ.get("PYTHONPATH", "")) if part
            ),
            PYTHONDONTWRITEBYTECODE="1",
            PYTHONIOENCODING="utf-8",
            PYTEST_DISABLE_PLUGIN_AUTOLOAD="1",
        )
        command = [
            sys.executable, "-B", "-m", "pytest",
            "-p", "ezspec.extension.pytest.plugin", "-p", "no:cacheprovider",
            "-o", "tmp_path_retention_policy=all",
            "-o", "tmp_path_retention_count=1000000",
            *arguments,
        ]
        result = subprocess.run(
            command, cwd=tmp_path, env=environment,
            capture_output=True, text=True, encoding="utf-8", timeout=45,
        )
        result.output = result.stdout + result.stderr
        return result

    return tmp_path, run


def _row_spec(*, then="assert env.geti('value') > 0"):
    return f'''
from pathlib import Path
import pytest
from ezspec import EzFeature, EzScenarioOutline, Feature

def event(message):
    with Path("events.txt").open("a", encoding="utf-8") as stream:
        stream.write(message + "\\n")

@pytest.fixture
def resource():
    event("setup")
    yield "resource"
    event("teardown")

@EzFeature
class RowSpec:
    feature = Feature.New("row feature")

    @EzScenarioOutline(examples={_CASES!r})
    def check_row(self, resource):
        event("build:" + resource)
        def verify(env):
            event(f"row:{{env.gets('value')}}:{{env.getExecutionCount()}}")
            {then}
        return self.feature.defineScenarioOutline("read row").Then("value <value>", verify)
'''


def test_collection_lists_rows_without_building_or_running_fixtures(spec_runner):
    path, run = spec_runner
    result = run(_row_spec(), "--collect-only", "-q")
    assert result.returncode == 0, result.output
    assert "3 tests collected" in result.output
    for code in ("A", "B", "C"):
        assert f"RowSpec::check_row[{code}]" in result.output
    assert not (path / "events.txt").exists()


def test_exact_node_selection_runs_only_one_row_with_original_index(spec_runner):
    path, run = spec_runner
    result = run(_row_spec(), "test_spec.py::RowSpec::check_row[B]", "-q")
    assert result.returncode == 0, result.output
    assert "1 passed" in result.output
    assert (path / "events.txt").read_text(encoding="utf-8").splitlines() == [
        "setup", "build:resource", "row:20:2", "teardown",
    ]


def test_each_row_has_fixture_lifecycle_and_steps_are_not_accumulated(spec_runner):
    path, run = spec_runner
    result = run(_row_spec(), "-q", "--ezspec-steps")
    assert result.returncode == 0, result.output
    assert "3 passed" in result.output
    assert "[Success] Then value <20>" in result.output
    events = (path / "events.txt").read_text(encoding="utf-8").splitlines()
    assert events == [
        "setup", "build:resource", "row:10:1", "teardown",
        "setup", "build:resource", "row:20:2", "teardown",
        "setup", "build:resource", "row:30:3", "teardown",
    ]


def test_failure_is_attributed_to_one_row_and_others_still_execute(spec_runner):
    path, run = spec_runner
    result = run(_row_spec(then="assert env.geti('value') != 20, 'bad row'"), "-q")
    assert result.returncode == 1, result.output
    assert "1 failed, 2 passed" in result.output
    assert "RowSpec::check_row[B]" in result.output
    assert "[Failure] Then value <20>" in result.output
    assert "ezSpec steps" in result.output
    assert "row:30:3" in (path / "events.txt").read_text(encoding="utf-8")


def test_fail_fast_remains_a_pytest_policy(spec_runner):
    path, run = spec_runner
    result = run(_row_spec(then="assert False, 'stop here'"), "-x", "-q")
    assert result.returncode == 1, result.output
    assert "1 failed" in result.output
    events = (path / "events.txt").read_text(encoding="utf-8")
    assert "row:10:1" in events
    assert "row:20:2" not in events


def test_legacy_fixture_and_parametrize_work_in_both_decorator_orders(spec_runner):
    _, run = spec_runner
    result = run('''
        import pytest
        from ezspec import EzFeature, EzScenario

        @EzFeature
        class LegacySpec:
            @EzScenario
            @pytest.mark.parametrize("number", [1, 2])
            def first_order(self, tmp_path, number):
                assert tmp_path.is_dir()
                assert number > 0

            @pytest.mark.parametrize("number", [1, 2])
            @EzScenario
            def second_order(self, number, tmp_path):
                assert tmp_path.is_dir()
                assert number > 0

        @EzScenario
        def module_fixture(tmp_path):
            assert tmp_path.is_dir()
    ''', "-q")
    assert result.returncode == 0, result.output
    assert "5 passed" in result.output


def test_rows_combine_with_standard_parameters(spec_runner):
    _, run = spec_runner
    result = run(f'''
        import pytest
        from ezspec import EzFeature, EzScenarioOutline, Feature
        @EzFeature
        class MatrixSpec:
            feature = Feature.New("matrix")

            @pytest.mark.parametrize("factor", [2, 3])
            @EzScenarioOutline(examples={_CASES!r})
            def product(self, factor, tmp_path):
                def check(env):
                    assert factor in (2, 3)
                    assert tmp_path.is_dir()
                    assert env.geti("value") > 0
                return self.feature.defineScenarioOutline("matrix").Then("value <value>", check)
    ''', "-q")
    assert result.returncode == 0, result.output
    assert "6 passed" in result.output


def test_rows_combine_with_keyword_parametrize_arguments(spec_runner):
    _, run = spec_runner
    result = run(f'''
        import pytest
        from ezspec import EzScenarioOutline, Feature
        feature = Feature.New("keyword parameters")

        @pytest.mark.parametrize(argnames="factor", argvalues=[2, 3])
        @EzScenarioOutline(examples={_CASES!r})
        def product(factor):
            def check(env):
                assert factor in (2, 3)
                assert env.geti("value") > 0
            return feature.defineScenarioOutline("matrix").Then("<value>", check)
    ''', "-q")
    assert result.returncode == 0, result.output
    assert "6 passed" in result.output


def test_header_only_is_a_noop_even_with_strict_empty_parameter_setting(spec_runner):
    _, run = spec_runner
    result = run('''
        from ezspec import EzFeature, EzScenarioOutline, Feature
        @EzFeature
        class EmptySpec:
            feature = Feature.New("empty")
            @EzScenarioOutline(examples="| value |")
            def empty(self):
                raise AssertionError("declaration must not run")
    ''', "-q", "-o", "empty_parameter_set_mark=fail_at_collect", "--ezspec-steps")
    assert result.returncode == 0, result.output
    assert "1 passed" in result.output
    assert "no-examples" in result.output


@pytest.mark.parametrize("source, message", [("[]", "at least an example"), ("None", "NoneType")])
def test_explicit_invalid_examples_fail_collection(spec_runner, source, message):
    _, run = spec_runner
    result = run(f'''
        from ezspec import EzScenarioOutline
        @EzScenarioOutline(examples={source})
        def invalid():
            raise AssertionError("must not run")
    ''', "--collect-only", "-q")
    assert result.returncode != 0
    assert "invalid Examples" in result.output
    assert message in result.output


def test_new_mode_rejects_wrong_return_type(spec_runner):
    _, run = spec_runner
    result = run('''
        from ezspec import EzScenarioOutline
        @EzScenarioOutline(examples="| value |\\n| 1 |")
        def invalid():
            return None
    ''', "-q")
    assert result.returncode == 1, result.output
    assert "must return an OutlineDefinition" in result.output


def test_dynamic_outline_uses_the_same_row_contract(spec_runner):
    _, run = spec_runner
    result = run('''
        from ezspec import EzDynamicScenarioOutline, Feature
        feature = Feature.New("dynamic")
        @EzDynamicScenarioOutline(examples="| value |\\n| 1 |\\n| 2 |")
        def dynamic():
            return feature.defineScenarioOutline("dynamic").Then("<value>", lambda env: None)
    ''', "-q")
    assert result.returncode == 0, result.output
    assert "2 passed" in result.output


def test_rule_context_and_background_reach_each_selected_row(spec_runner):
    _, run = spec_runner
    result = run('''
        from ezspec import EzFeature, EzRule, EzScenarioOutline, Feature
        @EzFeature
        @EzRule("VIP")
        class RuleSpec:
            feature = Feature.New("rule")
            vip = feature.NewRule("VIP")
            vip.newBackground("shared").Given("user", lambda env: env.put("user", "Ada")).Execute()

            @EzScenarioOutline(examples="| value |\\n| 1 |\\n| 2 |")
            def check(self):
                definition = self.feature.defineScenarioOutline("uses rule")
                assert definition.rule is self.vip
                def verify(env):
                    assert env.gets("user") == "Ada"
                return definition.Then("<value>", verify)
    ''', "-q")
    assert result.returncode == 0, result.output
    assert "2 passed" in result.output


def test_internal_case_parameter_is_reserved(spec_runner):
    _, run = spec_runner
    result = run('''
        from ezspec import EzScenarioOutline
        @EzScenarioOutline(examples="| value |\\n| 1 |")
        def invalid(_ezspec_case):
            pass
    ''', "--collect-only", "-q")
    assert result.returncode != 0
    assert "_ezspec_case is reserved" in result.output


def test_keyword_parametrize_cannot_override_internal_case(spec_runner):
    _, run = spec_runner
    result = run('''
        import pytest
        from ezspec import EzScenarioOutline
        @pytest.mark.parametrize(argnames="_ezspec_case", argvalues=[None], indirect=True)
        @EzScenarioOutline(examples="| value |\\n| 1 |")
        def invalid():
            raise AssertionError("must not run")
    ''', "--collect-only", "-q")
    assert result.returncode != 0
    assert "_ezspec_case is reserved" in result.output


def test_generator_callback_is_a_failed_row_not_a_success(spec_runner):
    _, run = spec_runner
    result = run('''
        from ezspec import EzFeature, EzScenarioOutline, Feature
        def assertion(env):
            assert False, "must not silently pass"
            yield None
        @EzFeature
        class LazySpec:
            feature = Feature.New("lazy callback")
            @EzScenarioOutline(examples="| value |\\n| 1 |")
            def check(self):
                return self.feature.defineScenarioOutline("must fail").Then(
                    "check <value>", lambda env: assertion(env)
                )
    ''', "-q")
    assert result.returncode == 1, result.output
    assert "1 failed" in result.output
    assert "must be synchronous" in result.output
    assert "[Failure] Then check <1>" in result.output


def test_exact_selection_report_keeps_catalog_and_only_selected_runtime(spec_runner):
    path, run = spec_runner
    result = run(
        _row_spec(), "test_spec.py::RowSpec::check_row[B]", "-q",
        "--ezspec-report", "--ezspec-report-dir", "reports",
    )
    assert result.returncode == 0, result.output
    report_dir = path / "reports"
    execution = json.loads((report_dir / "test_spec.RowSpec.execution.json").read_text(encoding="utf-8"))
    assert execution["totalRows"] == 3
    assert execution["selectedRows"] == execution["startedRows"] == execution["completedRows"] == 1
    assert [item["id"] for item in execution["items"] if item["selected"]] == ["B"]
    feature = json.loads((report_dir / "test_spec.RowSpec.json").read_text(encoding="utf-8"))
    outlines = [s for r in feature["ruleDtos"] for s in r["specificationElementDtos"]]
    assert len(outlines) == 1
    outline = outlines[0]
    assert len(outline["runtimeScenarioDtos"]) == 1
    assert len(outline["allExampleDtos"][0]["tableDto"]["rows"]) == 3
    assert outline["allExampleDtos"][0]["tableDto"]["RawData"] == _CASES
    assert outline["runtimeScenarioDtos"][0]["stepDtos"][0]["description"] == "value <20>"


def test_fully_deselected_feature_still_reports_zero_selected_rows(spec_runner):
    path, run = spec_runner
    result = run(
        _row_spec(), "-q", "-k", "no_matching_test_here",
        "--ezspec-report", "--ezspec-report-dir", "reports",
    )
    assert result.returncode == 5, result.output  # Normal pytest no-tests-selected code.
    snapshot = json.loads((path / "reports/test_spec.RowSpec.execution.json").read_text(encoding="utf-8"))
    assert snapshot["totalRows"] == 3
    assert snapshot["selectedRows"] == snapshot["startedRows"] == snapshot["completedRows"] == 0
    assert not (path / "events.txt").exists()


@pytest.mark.parametrize("phase", ["setup", "teardown"])
def test_fixture_phase_errors_survive_in_execution_report(spec_runner, phase):
    path, run = spec_runner
    source = _row_spec()
    if phase == "setup":
        source = source.replace('yield "resource"', 'raise RuntimeError("fixture broken")\n    yield "resource"')
    else:
        source = source.replace('event("teardown")', 'event("teardown")\n    raise RuntimeError("fixture broken")')
    result = run(
        source, "test_spec.py::RowSpec::check_row[B]", "-q",
        "--ezspec-report", "--ezspec-report-dir", "reports",
    )
    assert result.returncode == 1, result.output
    assert "INTERNALERROR" not in result.output
    snapshot = json.loads((path / "reports/test_spec.RowSpec.execution.json").read_text(encoding="utf-8"))
    record = next(item for item in snapshot["items"] if item["selected"])
    assert record["attemptCount"] == 1
    attempt = record["attempts"][0]
    assert attempt["phases"][phase]["outcome"] == "failed"
    assert "fixture broken" in attempt["phases"][phase]["error"]
    assert bool(attempt["runtimeScenarioDto"]) is (phase == "teardown")


@pytest.mark.parametrize("phase", ["setup", "teardown"])
def test_header_only_reports_fixture_errors_in_text_and_terminal(spec_runner, phase):
    path, run = spec_runner
    source = _row_spec().replace(repr(_CASES), repr("| value |"))
    if phase == "setup":
        source = source.replace('yield "resource"', 'raise RuntimeError("empty fixture broken")\n    yield "resource"')
    else:
        source = source.replace('event("teardown")', 'event("teardown")\n    raise RuntimeError("empty fixture broken")')
    result = run(
        source, "-q", "--ezspec-steps", "--ezspec-report",
        "--ezspec-report-dir", "reports",
    )
    assert result.returncode == 1, result.output
    assert f"pytest {phase}: failed" in result.output
    report = (path / "reports/test_spec.RowSpec.txt").read_text(encoding="utf-8")
    assert "0 列，未執行步驟" in report
    assert f"pytest {phase}: failed" in report
    snapshot = json.loads((path / "reports/test_spec.RowSpec.execution.json").read_text(encoding="utf-8"))
    assert snapshot["totalRows"] == snapshot["startedRows"] == snapshot["completedRows"] == 0
    assert snapshot["items"][0]["attempts"][0]["phases"][phase]["outcome"] == "failed"
    assert "build:" not in (path / "events.txt").read_text(encoding="utf-8")
