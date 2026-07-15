from ezspec.examples import Example, Examples


RAW = """
| price | vat  | total |
| 20000 | 0.05 | 21000 |
| 10000 | 0.01 | 10100 |
"""


def test_examples_factory_and_named_example():
    unnamed = Examples.New(RAW)
    named = Example("tax examples", "Calculate tax.", RAW)

    assert unnamed.getName() == ""
    assert named.getName() == "tax examples"
    assert named.getDescription() == "Calculate tax."
    assert named.getTable().get("price") == "20000"


def test_example_row_as_table_and_copy_are_independent():
    source = Example("tax examples", "Calculate tax.", RAW)
    copied = Example(source)

    assert source.rowAsTable(1).get("total") == "10100"
    copied.clear()
    assert len(source.getTable().rows()) == 2
    assert len(copied.getTable().rows()) == 0


def test_example_renders_gherkin_text():
    example = Example("tax examples", "Calculate tax.", RAW)

    rendered = str(example)
    assert rendered.startswith("\nExamples: tax examples\nCalculate tax.\n")
    assert "price" in rendered
    assert "21000" in rendered
