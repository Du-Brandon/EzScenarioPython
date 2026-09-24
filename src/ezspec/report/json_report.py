"""JSON rendering for executed ezSpec feature trees.

Python implementation using the standard json module and ezSpec's DTO schema.
See NOTICE and docs/SOURCE_PROVENANCE.md for the schema's source and attribution.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from .dto import FeatureDto

if TYPE_CHECKING:
    from ezspec.keyword import Feature


def render_json(
    feature: "Feature | FeatureDto",
    *,
    indent: int | None = None,
) -> str:
    """Render a feature using the field names of Java ``ezspec-report``.

    Compact output matches Jackson's default formatting. Passing ``indent``
    produces human-readable JSON while preserving non-ASCII feature text.
    """

    dto = feature if isinstance(feature, FeatureDto) else FeatureDto.from_feature(feature)
    separators = (",", ":") if indent is None else None
    return json.dumps(
        dto.to_dict(),
        ensure_ascii=False,
        indent=indent,
        separators=separators,
    )
