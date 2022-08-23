from pathlib import Path
from yatotem2scdl.conversion import ConvertisseurTotemBudget

from functools import cache

_BUDGET_XSLT = Path(__file__).parent / "totem2xmlcsv.xsl"


@cache
def make_or_get_budget_convertisseur() -> ConvertisseurTotemBudget:
    return ConvertisseurTotemBudget(xslt_budget=_BUDGET_XSLT)
