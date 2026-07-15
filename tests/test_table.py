import pytest

from ezspec.table import Header, Row, Table


CLEAN_TABLE = """|    owner          |   point-s      |   status Points  |
|    Jill           |   $100,000     |   80 0           |
|    Teddy Chen     |   50000        |   50.0           |"""

DIRTY_PREFIX_TABLE = """Given the following table:
                               |    owner          |   point-s      |   status Points  |
                               |    Jill           |   $100,000     |   80 0           |
                               |    Teddy Chen     |   50000        |   50.0           |
                               """

DIRTY_POSTFIX_TABLE = """|    owner          |   point-s      |   status Points  |
|    Jill           |   $100,000     |   80 0           |
|    Teddy Chen     |   50000        |   50.0           |
This is a noise string
"""


@pytest.mark.parametrize(
    "table_data",
    [CLEAN_TABLE, DIRTY_PREFIX_TABLE, DIRTY_POSTFIX_TABLE],
)
def test_create_tables_with_clean_and_dirty_data(table_data: str) -> None:
    table = Table(table_data)

    assert table.header().size() == 3
    assert len(table.rows()) == 2
    assert table.header().header() == ("owner", "point-s", "status Points")
    assert table.row(0).columns() == ("Jill", "$100,000", "80 0")
    assert table.row(1).columns() == ("Teddy Chen", "50000", "50.0")
    assert table.getRawData() == CLEAN_TABLE


def test_read_table_by_index_header_and_first_column() -> None:
    table = Table(
        """| owner | points | statusPoints |
        | Jill | 100,000 | 800 |
        | Jow | 50,000 | 50 |"""
    )

    assert table.get(0) == "Jill"
    assert table.get("points") == "100,000"
    assert table.get("missing") == ""
    assert table.row(0).get("owner") == "Jill"
    assert table.row("Jow").get(1) == "50,000"
    assert table.lastRow().get("statusPoints") == "50"
    assert table.row(0).getOrEmpty("missing") == ""


def test_unknown_header_and_row_raise_clear_errors() -> None:
    table = Table("| owner | points |\n| Jill | 100 |")

    with pytest.raises(RuntimeError, match="Header column 'status' not found"):
        table.row(0).get("status")
    with pytest.raises(RuntimeError, match="first column 'Jow' not found"):
        table.row("Jow")


def test_programmatic_table_and_copy_are_independent() -> None:
    header = Header.valueOf(["owner", "points"])
    table = Table(header)
    table.addRow(["Jill", "100\n"])
    table.addRow(Row(header, ["Jow", "50"], 1))
    copied = Table(table)

    table.clear()

    assert copied.header().header() == ("owner", "points")
    assert copied.row("Jill").get("points") == "100"
    assert copied.row("Jow").get(1) == "50"


def test_clear_removes_header_and_rows() -> None:
    table = Table("| owner | points |\n| Jill | 100 |")

    table.clear()

    assert table.header().size() == 0
    assert table.rows() == ()


def test_contains_table_and_string_rendering() -> None:
    table = Table("| owner | points |\n| Jill | 100 |")

    assert Table.containsTable("data:\n | owner |")
    assert not Table.containsTable("no tabular data")
    assert str(table) == "|\towner\t|\tpoints\t|\n|  Jill  \t|   100   \t|\n"


def test_raw_text_without_a_table_is_rejected() -> None:
    with pytest.raises(ValueError, match="does not contain a table"):
        Table("plain text")
