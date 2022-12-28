from dataclasses import dataclass, asdict
from typing import Optional

from app.shared.client_api_sirene import Etablissement

from yatotem2scdl.conversion import EtapeBudgetaire

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
            est_siege=str(etablissement.est_siege),
        )


# année - siret - etapes
RessourcesBudgetairesDisponibles = dict[str, dict[str, set[EtapeBudgetaire]]]


@dataclass()
class InfoBudgetDisponiblesApi:
    """Informations sur les ressources budget disponibles pour un siren donné"""

    siren: str
    ressources_disponibles: RessourcesBudgetairesDisponibles
    infos_etablissements: dict[str, InfosEtablissement]  # siret - infos

    def __serialize_v(self, v):
        if type(v) is dict:
            return {k: self.__serialize_v(v) for k, v in v.items()}
        if type(v) is set:
            return [self.__serialize_v(v) for v in v]
        if isinstance(v, EtapeBudgetaire):
            return str(v)
        return v

    def to_api_answer(self) -> dict:
        factory = lambda x: {k: self.__serialize_v(v) for (k, v) in x if v is not None}
        return asdict(self, dict_factory=factory)


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

    def to_api_answer(self) -> dict:
        factory = lambda x: {k: v for (k, v) in x if v is not None}
        return asdict(self, dict_factory=factory)


@dataclass()
class LigneBudgetMarqueBlancheApi:
    """Ligne budget provenant de la marque blanche. Voir documentation API"""

    fonction_code: Optional[str]
    compte_nature_code: str
    recette: bool
    montant: float

@dataclass()
class PdcInfo:
    annee: str
    nomenclature: str

@dataclass()
class GetBudgetMarqueBlancheApiResponse:
    """Réponse API. Voir documentation API"""

    etape: EtapeBudgetaire
    annee: int
    siret: str
    pdc_info: PdcInfo
    lignes: list[LigneBudgetMarqueBlancheApi]

    def __serialize_v(self, v):
        if isinstance(v, EtapeBudgetaire):
            return str(v)
        return v

    def to_api_answer(self) -> dict:
        factory = lambda x: {k: self.__serialize_v(v) for (k, v) in x if v is not None}
        return asdict(self, dict_factory=factory)
