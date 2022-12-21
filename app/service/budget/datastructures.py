from pathlib import Path
from typing import NamedTuple

from yatotem2scdl.conversion import TotemBudgetMetadata

TotemMetadataTuple = NamedTuple(
    "TotemMetadataTuple",
    [
        ("xml_fp", Path),
        ("metadata", TotemBudgetMetadata),
    ],
)