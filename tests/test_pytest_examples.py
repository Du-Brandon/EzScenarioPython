"""Tests for sharing scenario-outline examples with pytest."""

from __future__ import annotations

import pytest

from ezspec.extension.pytest import PytestExamples
from ezspec.keyword import Example


class tax_calculation_examples(PytestExamples):
    def getDescription(self) -> str:
        return "Calculate tax."

    def getExamplesRawData(self) -> str:
        return """
            | tax_excluded | vat_rate | total_price |
            | 20000        | 0.05     | 21000       |
            | 10000        | 0.01     | 10100       |
            | 35000        | 0.10     | 38500       |
        """


TAX_EXAMPLES = tax_calculation_examples()


def test_get_instantiates_subclass_and_returns_example() -> None:
    example = PytestExamples.get(tax_calculation_examples)

    assert isinstance(example, Example)
    assert example.getName() == "Tax calculation"
    assert example.getDescription() == "Calculate tax."
    assert example.getTable().row(0).get("total_price") == "21000"
    assert example.getTable().row(2).get(1) == "0.10"


def test_camel_and_snake_case_entries_are_compatible() -> None:
    assert TAX_EXAMPLES.getName() == TAX_EXAMPLES.get_name()
    assert TAX_EXAMPLES.getDescription() == TAX_EXAMPLES.get_description()
    assert (
        TAX_EXAMPLES.getExamplesRawData()
        == TAX_EXAMPLES.get_examples_raw_data()
    )
    assert str(TAX_EXAMPLES.getTable()) == str(TAX_EXAMPLES.get_table())


@pytest.mark.parametrize(TAX_EXAMPLES.parameters(), TAX_EXAMPLES.rows())
def test_rows_can_drive_pytest_parametrize(
    tax_excluded: str,
    vat_rate: str,
    total_price: str,
) -> None:
    expected_total = float(tax_excluded) * (1 + float(vat_rate))
    assert float(total_price) == expected_total


def test_provide_arguments_is_an_alias_for_rows() -> None:
    assert TAX_EXAMPLES.provide_arguments() == TAX_EXAMPLES.rows()


@pytest.mark.parametrize("invalid", [object, object(), PytestExamples])
def test_get_rejects_non_concrete_examples_types(invalid: object) -> None:
    with pytest.raises(TypeError, match="PytestExamples"):
        PytestExamples.get(invalid)  # type: ignore[arg-type]


def test_get_requires_a_no_argument_constructor() -> None:
    class requires_an_argument_examples(PytestExamples):
        def __init__(self, value: str) -> None:
            self.value = value

    with pytest.raises(TypeError, match="no-argument constructor"):
        PytestExamples.get(requires_an_argument_examples)


def test_raw_data_must_be_text() -> None:
    class invalid_raw_data_examples(PytestExamples):
        def getExamplesRawData(self) -> str:
            return None  # type: ignore[return-value]

    with pytest.raises(TypeError, match="must return str"):
        invalid_raw_data_examples().getTable()


def test_rows_validate_the_number_of_values() -> None:
    class uneven_examples(PytestExamples):
        def getExamplesRawData(self) -> str:
            return """
                | first | second |
                | only-one |
            """

    with pytest.raises(ValueError, match="expected 2"):
        uneven_examples().rows()
