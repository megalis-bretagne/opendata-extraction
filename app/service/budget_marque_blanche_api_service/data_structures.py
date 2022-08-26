from dataclasses import dataclass
from pathlib import Path
from typing import NamedTuple, Optional

from yatotem2scdl.conversion import TotemBudgetMetadata, EtapeBudgetaire


_EtabInfo = NamedTuple(
    "_EtabInfo",
    [
        ("denomination", str),
        ("siret_siege", int),
    ],
)

_TotemAndMetadata = NamedTuple(
    "_TotemAndMetadata",
    [
        ("xml_fp", Path),
        ("metadata", TotemBudgetMetadata),
    ],
)

@dataclass()
class ElementPlanDeCompte:
    code: str
    libelle: str
    parent_code: Optional[str]

@dataclass()
class RefFonctionnelleBudgetMarqueBlancheApi(ElementPlanDeCompte):
    """Reférence fonctionnelle du plan de compte"""

@dataclass()
class CompteNatureMarqueBlancheApi(ElementPlanDeCompte):
    """Comptes natures du plan de compte"""

@dataclass()
class GetInfoPlanDeComptesBudgetMarqueBlancheApi:
    """Réponse API. Voir documentation API"""

    references_fonctionnelles: dict[str, RefFonctionnelleBudgetMarqueBlancheApi]
    comptes_nature: dict[str, CompteNatureMarqueBlancheApi]


@dataclass()
class LigneBudgetMarqueBlancheApi:
    """Ligne budget provenant de la marque blanche. Voir documentation API"""

    fonction_code: Optional[str]
    recette: bool
    montant: float


@dataclass()
class GetBudgetMarqueBlancheApiResponse:
    """Réponse API. Voir documentation API"""

    etape: EtapeBudgetaire
    annee: int
    siren: str
    siret_siege: str
    denomination_siege: str
    lignes: list[LigneBudgetMarqueBlancheApi]
