"""Small formatting helpers retained from ezSpec's ``SpecUtils``.

Adapted from ezSpec's SpecUtils.java. Original Java author: Teddy Chen.
Modified for Python; see NOTICE and docs/SOURCE_PROVENANCE.md.
"""

from __future__ import annotations

import re


class SpecUtils:
    @staticmethod
    def getReplacedUnderscores(name: str) -> str:
        return name.replace("_", " ")

    @staticmethod
    def center(value: str, width: int) -> str:
        padding = (width - len(value)) // 2
        if padding <= 0:
            return value
        return f"{'':>{padding}}{value}{'':>{padding}}"

    @staticmethod
    def deleteEndWithNewLine(value: str) -> str:
        return re.sub(r"[\n\r]+$", "", value)


get_replaced_underscores = SpecUtils.getReplacedUnderscores
center = SpecUtils.center
delete_end_with_new_line = SpecUtils.deleteEndWithNewLine
