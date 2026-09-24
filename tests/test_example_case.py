from dataclasses import FrozenInstanceError

import pytest

from ezspec import Example, ExampleCase, normalize_examples
from ezspec.extension.pytest.examples import PytestExamples


class NamedExamples(PytestExamples):
    def getDescription(self):
        return "named data"

    def getExamplesRawData(self):
        return "| example_code | value |\n| KNOWN | 7 |"


def test_catalog_snapshots_multiple_sources_and_recreates_examples():
    original = Example("named", "first", "| example_code | value |\n| A | 1 |")
    catalog = normalize_examples(
        [original, NamedExamples(), "| value |\n| three |"]
    )

    assert [(case.example_index, case.row_index, case.index, case.id) for case in catalog.cases] == [
        (0, 0, 0, "A"),
        (1, 0, 1, "KNOWN"),
        (2, 0, 2, "e3-r1"),
    ]
    original.clear()
    first = catalog.to_examples()
    second = catalog.to_examples()
    assert first is not second
    assert first[0] is not second[0]
    assert first[0].getName() == "named"
    assert first[0].getDescription() == "first"
    assert first[0].getTable().get("value") == "1"
    assert first[0].getTable().getRawData() == "| example_code | value |\n| A | 1 |"
    first[0].clear()
    assert catalog.to_examples()[0].getTable().get("value") == "1"


def test_case_is_frozen_and_to_table_returns_independent_tables():
    case = normalize_examples("| value |\n| 42 |").cases[0]
    assert isinstance(case, ExampleCase)
    with pytest.raises(FrozenInstanceError):
        case.id = "changed"
    first = case.to_table()
    second = case.to_table()
    assert first is not second
    first.clear()
    assert second.get("value") == "42"


def test_ids_are_ascii_unique_and_stable_with_duplicate_codes():
    source = """| example_code | value |
| 同名/1 | A |
| 同名/1 | B |
| ADD01 | C |
"""
    catalog = normalize_examples((source, "| value |\n| D |"))
    ids = [case.id for case in catalog.cases]
    assert ids == [case.id for case in normalize_examples((source, "| value |\n| D |")).cases]
    assert len(set(ids)) == len(ids)
    assert all(case_id.isascii() and "[" not in case_id and "]" not in case_id for case_id in ids)
    assert ids[0].endswith("-e1-r1")
    assert ids[1].endswith("-e1-r2")
    assert ids[2] == "ADD01"
    assert ids[3] == "e2-r1"


def test_header_only_and_invalid_sources_are_distinct():
    catalog = normalize_examples("| example_code | value |")
    assert catalog.cases == ()
    assert len(catalog.to_examples()) == 1
    with pytest.raises(RuntimeError, match="at least an example"):
        normalize_examples([])
    with pytest.raises(TypeError, match="unsupported example type"):
        normalize_examples(None)
    with pytest.raises(ValueError, match="has 1 values; expected 2"):
        normalize_examples("| first | second |\n| only |")
