"""Gherkin-style data-table models."""

from __future__ import annotations

import re
from collections.abc import Iterable, Sequence
from typing import overload


class Header:
    """A table header."""

    def __init__(self, data: Iterable[str] = ()) -> None:
        self._header = list(data)

    @classmethod
    def valueOf(cls, data: Iterable[str]) -> Header:
        return cls(data)

    value_of = valueOf

    @classmethod
    def create(cls) -> Header:
        return cls()

    def reset(self, new_header: Iterable[str]) -> None:
        self._header[:] = new_header

    def get(self, index: int) -> str:
        return self._header[index]

    def header(self) -> tuple[str, ...]:
        return tuple(self._header)

    def size(self) -> int:
        return len(self._header)

    def clear(self) -> None:
        self._header.clear()

    def __str__(self) -> str:
        return "|" + "".join(
            f"\t{column}\t|" for column in self._header if column
        )


class Row:
    """One table row, addressable by column index or header name."""

    def __init__(
        self,
        header: Header,
        columns: Iterable[str],
        index: int = 0,
    ) -> None:
        self._header = header
        self._columns = list(columns)
        self.index = index

    @overload
    def get(self, column: int) -> str: ...

    @overload
    def get(self, column: str) -> str: ...

    def get(self, column: int | str) -> str:
        if isinstance(column, int):
            return self._columns[column]
        for index, name in enumerate(self._header.header()):
            if name == column:
                return self._columns[index]
        raise RuntimeError(f"Header column '{column}' not found.")

    def getOrEmpty(self, column_name: str) -> str:
        for index, name in enumerate(self._header.header()):
            if name == column_name:
                return self._columns[index]
        return ""

    get_or_empty = getOrEmpty

    def columns(self) -> tuple[str, ...]:
        return tuple(self._columns)

    def __str__(self) -> str:
        parts: list[str] = []
        for index, column in enumerate(self._columns):
            if not column:
                continue
            if Table.containsTable(column):
                nested = re.sub(r"[\n\r]+$", "", column)
                parts.append(f"\n<{self._header.get(index)}>\n{nested}")
                continue

            width = len(f"|\t{self._header.get(index)}\t|")
            padding = max((width - len(column)) // 2, 0)
            parts.append(f"{' ' * padding}{column}{' ' * padding}\t|")
        return "".join(parts)


class Table:
    """A parsed data table or a programmatically assembled table."""

    TABLE_SEPARATOR = "|"

    def __init__(
        self,
        source: str | Table | Header | None = None,
        rows: Iterable[Row] | None = None,
    ) -> None:
        self._raw_data: str | None = None

        if source is None:
            if rows is not None:
                raise TypeError("rows require a Header")
            self._header = Header.create()
            self._rows: list[Row] = []
        elif isinstance(source, str):
            if rows is not None:
                raise TypeError("rows cannot be supplied with raw table data")
            self._parse(source)
        elif isinstance(source, Table):
            if rows is not None:
                raise TypeError("rows cannot be supplied when copying a Table")
            self._raw_data = source._raw_data
            self._header = Header.valueOf(source.header().header())
            self._rows = [
                Row(self._header, row.columns(), row.index) for row in source.rows()
            ]
        elif isinstance(source, Header):
            self._header = source
            self._rows = list(rows or ())
        else:
            raise TypeError("source must be raw data, a Table, a Header, or None")

    def _parse(self, raw_data: str) -> None:
        cooked_lines = []
        for line in raw_data.splitlines():
            if self.TABLE_SEPARATOR not in line:
                continue
            cooked_lines.append(line[line.index(self.TABLE_SEPARATOR) :].strip())

        if not cooked_lines:
            raise ValueError("rawData does not contain a table")

        self._header = Header.valueOf(self._parse_columns(cooked_lines[0]))
        self._rows = []
        for index, line in enumerate(cooked_lines[1:]):
            columns = self._parse_columns(line)
            self._rows.append(Row(self._header, columns, index))
        self._raw_data = "\n".join(cooked_lines)

    @staticmethod
    def _parse_columns(line: str) -> list[str]:
        # Mirrors Java's split/filter behavior for compatibility.
        return [column.strip() for column in line.split("|") if column.strip()]

    def getRawData(self) -> str | None:
        return self._raw_data

    get_raw_data = getRawData

    @overload
    def get(self, column: int) -> str: ...

    @overload
    def get(self, column: str) -> str: ...

    def get(self, column: int | str) -> str:
        if isinstance(column, int):
            return self._rows[0].get(column)
        for index, name in enumerate(self._header.header()):
            if name == column:
                return self._rows[0].get(index)
        return ""

    def header(self) -> Header:
        return self._header

    def rows(self) -> tuple[Row, ...]:
        return tuple(self._rows)

    @overload
    def row(self, row: int) -> Row: ...

    @overload
    def row(self, row: str) -> Row: ...

    def row(self, row: int | str) -> Row:
        if isinstance(row, int):
            return self._rows[row]
        for candidate in self._rows:
            if candidate.get(0) == row:
                return candidate
        raise RuntimeError(f"Row which first column '{row}' not found.")

    def lastRow(self) -> Row:
        return self._rows[-1]

    last_row = lastRow

    def addRow(self, row: Row | Sequence[str]) -> None:
        if isinstance(row, Row):
            self._rows.append(row)
            return
        columns = [column[:-1] if column.endswith("\n") else column for column in row]
        self._rows.append(Row(self._header, columns, len(self._rows)))

    add_row = addRow

    def clear(self) -> None:
        self._header.clear()
        self._rows.clear()

    @staticmethod
    def containsTable(description: str) -> bool:
        return any(line.strip().startswith("|") for line in description.splitlines())

    contains_table = containsTable

    def __str__(self) -> str:
        body = "".join(f"\n|{row}" for row in self._rows)
        return f"{self._header}{body}\n"
