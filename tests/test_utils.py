from ezspec.tags import EzSpecTag
from ezspec.utils import SpecUtils


def test_replaces_underscores() -> None:
    assert SpecUtils.getReplacedUnderscores("vip_customer_checkout") == "vip customer checkout"


def test_centers_text_like_java_spec_utils() -> None:
    assert SpecUtils.center("abc", 7) == "  abc  "
    assert SpecUtils.center("abc", 3) == "abc"


def test_deletes_trailing_newlines_only() -> None:
    assert SpecUtils.deleteEndWithNewLine("hello\r\n\n") == "hello"


def test_tag_values_match_java_constants() -> None:
    assert EzSpecTag.Env.Dev == "Env.Development"
    assert EzSpecTag.TestType.Unit == "TestType.Unit"
    assert EzSpecTag.LivingDoc.EzSpec == "LivingDoc.EzSpec"
