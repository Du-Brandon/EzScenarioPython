import ezspec
from ezspec.exception import PendingException
from ezspec.extension.pytest import EzFeature, EzScenario
from ezspec.extension.utils import SpecUtils
from ezspec.feature import Feature as LegacyFeature
from ezspec.keyword import Feature, ScenarioEnvironment
from ezspec.keyword.table import Header, Row, Table


def test_canonical_packages_export_the_public_types() -> None:
    assert ezspec.Feature is Feature
    assert ezspec.ScenarioEnvironment is ScenarioEnvironment
    assert ezspec.PendingException is PendingException
    assert ezspec.EzFeature is EzFeature
    assert ezspec.EzScenario is EzScenario
    assert ezspec.Header is Header
    assert ezspec.Row is Row
    assert ezspec.Table is Table


def test_flat_module_path_remains_compatible() -> None:
    assert LegacyFeature is Feature


def test_extension_utilities_are_available_from_the_canonical_path() -> None:
    assert SpecUtils.getReplacedUnderscores("hello_world") == "hello world"
