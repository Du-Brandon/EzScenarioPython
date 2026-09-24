"""Immutable, collection-time snapshots of Scenario Outline examples."""

from __future__ import annotations

from dataclasses import dataclass

from .examples import Example, Examples
from .table import Header, Row, Table


@dataclass(frozen=True)
class ExampleCase:
    """One row, with coordinates that remain stable when other rows are skipped."""

    example_index: int
    row_index: int
    index: int
    id: str
    headers: tuple[str, ...]
    values: tuple[str, ...]

    def to_table(self) -> Table:
        header = Header(self.headers)
        return Table(header, [Row(header, self.values, self.row_index)])


@dataclass(frozen=True)
class _ExampleSnapshot:
    name: str
    description: str
    headers: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]
    raw_data: str | None

    def to_example(self) -> Example:
        header = Header(self.headers)
        table = Table(
            header,
            [Row(header, values, index) for index, values in enumerate(self.rows)],
        )
        # The parser's source text is also part of the legacy report model.
        # Rows still come from the detached snapshot if the original mutated.
        table._raw_data = self.raw_data
        return Example(self.name, self.description, table)


@dataclass(frozen=True)
class ExampleCatalog:
    """Detached examples and their flattened row catalog."""

    cases: tuple[ExampleCase, ...]
    _examples: tuple[_ExampleSnapshot, ...]

    def to_examples(self) -> tuple[Example, ...]:
        return tuple(snapshot.to_example() for snapshot in self._examples)


def _ascii_id(code: str) -> str:
    """Encode every unsafe UTF-8 byte without changing common ASCII codes."""
    encoded = code.encode("utf-8")
    return "".join(
        chr(byte)
        if (
            48 <= byte <= 57
            or 65 <= byte <= 90
            or 97 <= byte <= 122
            or byte in (45, 95)
        )
        else f"-x{byte:02X}"
        for byte in encoded
    )


def normalize_examples(
    source: str | Examples | list[object] | tuple[object, ...],
) -> ExampleCatalog:
    """Validate and freeze examples without retaining mutable source tables."""
    if isinstance(source, (list, tuple)):
        if not source:
            raise RuntimeError("require at least an example")
        values = source
    else:
        values = (source,)

    snapshots: list[_ExampleSnapshot] = []
    for value in values:
        if isinstance(value, str):
            example = Example(value)
        elif isinstance(value, Examples):
            example = value.getExample()
        else:
            raise TypeError(f"unsupported example type: {type(value).__name__}")
        table = example.getTable()
        headers = table.header().header()
        rows = tuple(row.columns() for row in table.rows())
        for row_index, row in enumerate(rows):
            if len(row) != len(headers):
                raise ValueError(
                    f"example row {row_index} has {len(row)} values; "
                    f"expected {len(headers)}"
                )
        snapshots.append(
            _ExampleSnapshot(
                example.getName(),
                example.getDescription(),
                headers,
                rows,
                table.getRawData(),
            )
        )

    preliminary: list[
        tuple[int, int, int, str, tuple[str, ...], tuple[str, ...]]
    ] = []
    for example_index, snapshot in enumerate(snapshots):
        for row_index, row in enumerate(snapshot.rows):
            code = (
                row[snapshot.headers.index("example_code")]
                if "example_code" in snapshot.headers
                else ""
            )
            fallback = f"e{example_index + 1}-r{row_index + 1}"
            preliminary.append(
                (
                    example_index,
                    row_index,
                    len(preliminary),
                    _ascii_id(code) if code else fallback,
                    snapshot.headers,
                    row,
                )
            )

    frequencies: dict[str, int] = {}
    for _, _, _, case_id, _, _ in preliminary:
        frequencies[case_id] = frequencies.get(case_id, 0) + 1

    cases: list[ExampleCase] = []
    used: set[str] = set()
    for example_index, row_index, index, base_id, headers, row in preliminary:
        case_id = base_id
        if frequencies[case_id] > 1:
            case_id = f"{case_id}-e{example_index + 1}-r{row_index + 1}"
        suffix = 1
        while case_id in used:
            case_id = f"{base_id}-e{example_index + 1}-r{row_index + 1}-i{suffix}"
            suffix += 1
        used.add(case_id)
        cases.append(
            ExampleCase(example_index, row_index, index, case_id, headers, row)
        )
    return ExampleCatalog(tuple(cases), tuple(snapshots))
