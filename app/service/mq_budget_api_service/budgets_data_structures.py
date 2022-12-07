from dataclasses import dataclass
from pathlib import Path
from typing import NamedTuple, Optional

from app.shared.client_api_sirene import Etablissement

from yatotem2scdl.conversion import TotemBudgetMetadata, EtapeBudgetaire

_TotemAndMetadata = NamedTuple(
    "_TotemAndMetadata",
    [
        ("xml_fp", Path),
        ("metadata", TotemBudgetMetadata),
    ],
)

#
# API budget disponibles
#
@dataclass()
class InfosEtablissement:
    """Information sur un établissement donnée"""
    denomination: str
    siret: str
    enseigne: Optional[str]
    est_siege: str

    @staticmethod
    def from_api_sirene_etablissement(etablissement: Etablissement):
        return InfosEtablissement(
            denomination=etablissement.denomination_unite_legale,
            siret=etablissement.siret,
            enseigne=etablissement.enseigne,
            est_siege=str(etablissement.est_siege)
        )

# année - siret - etapes
RessourcesBudgetairesDisponibles = dict[str, dict[str, set[EtapeBudgetaire]]]

@dataclass()
class InfoBudgetDisponiblesApi:
    """Informations sur les ressources budget disponibles pour un siren donné"""
    siren: str
    ressources_disponibles: RessourcesBudgetairesDisponibles
    infos_etablissements: dict[str, InfosEtablissement] # siret - infos

#
# PDC et info budget
#
@dataclass()
class ElementNomenclaturePdc:
    """Element de nomenclature d'un PDC"""
    code: str
    libelle: str
    parent_code: Optional[str]

@dataclass()
class RefFonctionnelleBudgetMarqueBlancheApi(ElementNomenclaturePdc):
    """Reférence fonctionnelle du plan de compte"""

@dataclass()
class CompteNatureMarqueBlancheApi(ElementNomenclaturePdc):
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
    compte_nature_code: str
    recette: bool
    montant: float


@dataclass()
class GetBudgetMarqueBlancheApiResponse:
    """Réponse API. Voir documentation API"""

    etape: EtapeBudgetaire
    annee: int
    siret: str
    lignes: list[LigneBudgetMarqueBlancheApi]
