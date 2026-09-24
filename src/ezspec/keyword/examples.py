"""Gherkin ``Examples`` data used by scenario outlines.

Adapted from ezSpec's Example.java and Examples.java.
Original Java author: Teddy Chen. Modified for Python;
see NOTICE and docs/SOURCE_PROVENANCE.md.
"""

from __future__ import annotations

from collections.abc import Sequence

from .table import Table


class Examples:
    """Factory/protocol-compatible base for a set of example rows."""

    @staticmethod
    def New(table_content: str) -> "Example":
        if table_content is None:
            raise TypeError("table content cannot be None")
        return Example(table_content)

    new = New

    def getName(self) -> str:
        raise NotImplementedError

    def getDescription(self) -> str:
        raise NotImplementedError

    def getTable(self) -> Table:
        raise NotImplementedError

    def getExample(self) -> "Example":
        return Example(self.getName(), self.getDescription(), self.getTable())

    get_name = getName
    get_description = getDescription
    get_table = getTable
    get_example = getExample


class Example(Examples):
    """A named Gherkin Examples table.

    Supported forms mirror the Java constructors::

        Example(table_content)
        Example(name, description, table_content)
        Example(existing_example)
    """

    KEYWORD = "Examples"

    def __init__(
        self,
        name_or_table: str | "Example",
        description: str | None = None,
        table_content: str | Table | None = None,
    ) -> None:
        if isinstance(name_or_table, Example):
            if description is not None or table_content is not None:
                raise TypeError("copy construction accepts only one Example")
            self._name = name_or_table.getName()
            self._description = name_or_table.getDescription()
            self._table = Table(name_or_table.getTable())
            return

        if name_or_table is None:
            raise TypeError("name/table content cannot be None")

        if description is None and table_content is None:
            self._name = ""
            self._description = ""
            self._table = Table(name_or_table)
            return

        if description is None or table_content is None:
            raise TypeError("name, description, and table content are required")

        self._name = name_or_table
        self._description = description
        self._table = Table(table_content)

    def clear(self) -> None:
        self._table.clear()

    def getName(self) -> str:
        return self._name

    def getDescription(self) -> str:
        return self._description

    def getTable(self) -> Table:
        return self._table

    def getExample(self) -> "Example":
        return self

    def rowAsTable(self, index: int) -> Table:
        rows: Sequence[object] = self._table.rows()
        return Table(self._table.header(), [rows[index]])

    get_name = getName
    get_description = getDescription
    get_table = getTable
    get_example = getExample
    row_as_table = rowAsTable

    def __str__(self) -> str:
        output = f"\n{self.KEYWORD}: {self._name}\n"
        if self._description:
            output += f"{self._description}\n"
        return output + str(self._table)
