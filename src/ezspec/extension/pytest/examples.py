"""pytest-compatible Gherkin examples.

This module is the Python counterpart of ezSpec's ``Junit5Examples``.  A
concrete subclass supplies a raw Gherkin table and can use the same data for
both a scenario outline and ``pytest.mark.parametrize``.
"""

from __future__ import annotations

from typing import Any

from ...keyword.examples import Example, Examples
from ...keyword.table import Table


class PytestExamples(Examples):
    """Base class for examples shared with pytest parametrization.

    Subclasses implement :meth:`getExamplesRawData` and
    :meth:`~ezspec.keyword.examples.Examples.getDescription`::

        class tax_calculation_examples(PytestExamples):
            def getDescription(self) -> str:
                return "Calculate tax."

            def getExamplesRawData(self) -> str:
                return "| net | rate | total |\n| 100 | 0.05 | 105 |"

    ``parameters()`` and ``rows()`` are suitable for direct use with
    ``pytest.mark.parametrize``.
    """

    def getName(self) -> str:
        simple_name = type(self).__name__
        display_name = simple_name.replace("_examples", "").replace("_", " ")
        return display_name[:1].upper() + display_name[1:]

    def get_description(self) -> str:
        """Snake-case compatibility entry for ``getDescription``."""

        return self.getDescription()

    @staticmethod
    def get(examples_type: type[PytestExamples]) -> Example:
        """Instantiate a concrete examples class and return its ``Example``.

        The explicit validation makes mistakes at the sample declaration site
        clearer than the reflection error produced by the Java implementation.
        """

        if not isinstance(examples_type, type):
            raise TypeError("examples_type must be a PytestExamples subclass")
        if not issubclass(examples_type, PytestExamples):
            raise TypeError("examples_type must be a PytestExamples subclass")
        if examples_type is PytestExamples:
            raise TypeError("PytestExamples itself is not a concrete example")

        try:
            instance = examples_type()
        except TypeError as error:
            raise TypeError(
                f"{examples_type.__name__} must have a no-argument constructor"
            ) from error

        return instance.getExample()

    def getTable(self) -> Table:
        raw_data = self.getExamplesRawData()
        if not isinstance(raw_data, str):
            raise TypeError("getExamplesRawData() must return str")
        return Table(raw_data)

    def getExamplesRawData(self) -> str:
        """Return raw Gherkin table data supplied by a subclass."""

        raise NotImplementedError

    def get_examples_raw_data(self) -> str:
        """Snake-case compatibility entry for ``getExamplesRawData``."""

        return self.getExamplesRawData()

    def parameters(self) -> tuple[str, ...]:
        """Return pytest parameter names derived from the table header."""

        return self.getTable().header().header()

    def rows(self) -> tuple[tuple[str, ...], ...]:
        """Return pytest parameter values derived from the example rows."""

        table = self.getTable()
        parameters = table.header().header()
        values = tuple(row.columns() for row in table.rows())

        for index, row in enumerate(values):
            if len(row) != len(parameters):
                raise ValueError(
                    "example row "
                    f"{index} has {len(row)} values; expected {len(parameters)}"
                )
        return values

    def provide_arguments(self) -> tuple[tuple[Any, ...], ...]:
        """JUnit-style alias for consumers that prefer provider terminology."""

        return self.rows()

    get_name = getName
    get_table = getTable


__all__ = ["PytestExamples"]
