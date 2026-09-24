"""Small, dependency-free Gherkin keyword catalogue for reports.

Python implementation informed by ezSpec's GherkinKeywords.java and its
English/Traditional Chinese report vocabulary. See NOTICE and
docs/SOURCE_PROVENANCE.md for source and project attribution.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType


@dataclass(frozen=True)
class GherkinKeywords:
    """The preferred display keyword for one Gherkin language."""

    code: str
    name: str
    native: str
    _keywords: Mapping[str, str]

    def getI18nKeyword(self, keyword: str) -> str:
        """Return the translated display form of ``keyword``."""

        normalized = keyword.replace("_", " ").strip().upper()
        try:
            return self._keywords[normalized]
        except KeyError as error:
            raise ValueError(f"Unsupported Gherkin keyword: {keyword}") from error

    get_i18n_keyword = getI18nKeyword


def _keywords(**values: str) -> Mapping[str, str]:
    return MappingProxyType(
        {
            key.replace("_", " ").strip().upper(): value.strip()
            for key, value in values.items()
        }
    )


ENGLISH = GherkinKeywords(
    code="en",
    name="English",
    native="English",
    _keywords=_keywords(
        and_="And",
        background="Background",
        but="But",
        examples="Examples",
        feature="Feature",
        given="Given",
        rule="Rule",
        scenario="Scenario",
        scenario_outline="Scenario Outline",
        then="Then",
        then_success="Then success",
        then_failure="Then failure",
        when="When",
    ),
)

TRADITIONAL_CHINESE = GherkinKeywords(
    code="zh-TW",
    name="Chinese traditional",
    native="繁體中文",
    _keywords=_keywords(
        and_="而且",
        background="背景",
        but="但是",
        examples="例子",
        feature="功能",
        given="假如",
        rule="規則",
        scenario="場景",
        scenario_outline="場景大綱",
        then="那麼",
        then_success="那麼成功",
        then_failure="那麼失敗",
        when="當",
    ),
)

_LANGUAGES = MappingProxyType(
    {
        "en": ENGLISH,
        "en-us": ENGLISH,
        "tw": TRADITIONAL_CHINESE,
        "zh-tw": TRADITIONAL_CHINESE,
    }
)


def get_gherkin_keywords(language: str | None = "en") -> GherkinKeywords:
    """Resolve a supported language code, including Python-friendly aliases."""

    normalized = "en" if language is None else language.strip().replace("_", "-").lower()
    try:
        return _LANGUAGES[normalized]
    except KeyError as error:
        supported = "en, tw, zh-TW"
        raise ValueError(
            f"Unsupported report language {language!r}; supported: {supported}"
        ) from error


__all__ = [
    "ENGLISH",
    "GherkinKeywords",
    "TRADITIONAL_CHINESE",
    "get_gherkin_keywords",
]
