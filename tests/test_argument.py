from ezspec.argument import Argument


def test_value_arguments_start_with_dollar_sign() -> None:
    assert Argument.create("$1").value() == "1"
    assert Argument.create("$1").key() == ""
    assert Argument.create("$80").value() == "80"
    assert Argument.create(r"$\$5").value() == r"\$5"
    assert Argument.create("$$5").value() == "$5"
    assert Argument.create("$$$5").value() == "$$5"
    assert Argument.create("$$$20$20").value() == "$$20$20"
    assert Argument.create("$vat:100").value() == "vat:100"
    assert Argument.create("$vat=100").value() == "vat=100"


def test_key_value_arguments_are_enclosed_in_dollar_curly_brackets() -> None:
    assert Argument.create("${price:21,000}").value() == "21,000"
    assert Argument.create("${price : 21,000}").key() == "price"
    assert Argument.create("${price= 21,000}").value() == "21,000"
    assert Argument.create("${price=21,000}").key() == "price"
    assert Argument.create("${gift =$$$keyboard}").value() == "$$$keyboard"


def test_argument_from_key_and_mutators_preserve_java_api() -> None:
    argument = Argument.fromKey("price")

    assert argument.key() == "price"
    assert argument.value() is None

    argument.value("100")
    argument.key("total")

    assert argument.key() == "total"
    assert argument.value() == "100"


def test_text_without_argument_has_no_key_or_value() -> None:
    argument = Argument.create("a $ without value")

    assert argument.key() is None
    assert argument.value() is None
