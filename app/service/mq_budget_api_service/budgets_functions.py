import logging
import functools

from pathlib import Path
from typing import Callable, Union

from .budgets_data_structures import (
    EtapeBudgetaire,
    GetBudgetMarqueBlancheApiResponse,
    GetInfoPlanDeComptesBudgetMarqueBlancheApi,
    LigneBudgetMarqueBlancheApi,
)

from app.shared.client_api_sirene import Etablissement

from .budgets_exceptions import (
    BudgetMarqueBlancheApiException,
    EtapeInvalideError,
    ImpossibleDextraireEtabInfoError,
)

from yatotem2scdl import EtapeBudgetaireInconnueErreur


from ._ExtracteurInfoPdc import _ExtracteurInfoPdc

# Les fichiers de plans de compte sont peu nombreux.
@functools.cache
def pdc_path_to_api_response(plan_de_comptes_path: Path):
    extracteur = _ExtracteurInfoPdc(plan_de_comptes_path)
    references_fonctionnelles = extracteur.extraire_references_fonctionnelles()
    comptes_nature = extracteur.extraire_comptes_nature()
    return GetInfoPlanDeComptesBudgetMarqueBlancheApi(
        references_fonctionnelles, comptes_nature
    )


def _etape_from_str(etape: str) -> EtapeBudgetaire:
    try:
        return EtapeBudgetaire.from_str(etape)
    except EtapeBudgetaireInconnueErreur as err:
        raise EtapeInvalideError(etape) from err


def _api_sirene_etablissement_siege(
    siren: str, logger: logging.Logger
) -> Etablissement:

    from app.shared.client_api_sirene.flask_functions import (
        etablissement_siege_pour_siren,
    )

    try:
        etablissement = etablissement_siege_pour_siren(siren)
        logger.debug(f"Voici l'établissement {etablissement}")
        return etablissement

    except Exception as err:
        raise ImpossibleDextraireEtabInfoError(siren) from err


def _api_sirene_etablissements(
    siren: str, logger: logging.Logger
) -> list[Etablissement]:

    from app.shared.client_api_sirene.flask_functions import etablissements_pour_siren

    try:
        etablissements = etablissements_pour_siren(siren)
        logger.debug(f"Voici les établissements pour le siren {etablissements}")
        return etablissements

    except Exception as err:
        raise ImpossibleDextraireEtabInfoError(siren) from err


def _wrap_in_budget_marque_blanche_api_ex(func):
    @functools.wraps(func)
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except BudgetMarqueBlancheApiException as err:
            raise err
        except Exception as err:
            raise BudgetMarqueBlancheApiException("Erreur inconnue") from err

    return inner


def _prune_montant_a_zero(func: Callable[..., GetBudgetMarqueBlancheApiResponse]):
    def filter_fn(ligne: LigneBudgetMarqueBlancheApi):
        return ligne.montant and ligne.montant != 0

    @functools.wraps(func)
    def inner(*args, **kwargs) -> GetBudgetMarqueBlancheApiResponse:
        answer = func(*args, **kwargs)

        lignes = answer.lignes
        pruned = list(filter(filter_fn, lignes))
        answer.lignes = pruned

        return answer

    return inner


def extraire_siren(siret: Union[str, int]) -> Union[str, int]:
    """Récupère le numéro siren à partir d'un SIRET

    Args:
        siret (Union[str, int]): numéro siret

    Raises:
        TypeError: Lorsque le siret n'est ni un int ni un str
        ValueError: Lorsque le siret n'a pas le bon format

    Returns:
        Union[str, int]: Le siren correspondant
    """

    siret_s: str
    if isinstance(siret, str):
        siret_s = siret
    elif type(siret) == int:
        siret_s = str(siret)
    else:
        raise TypeError(f"{siret} devrait être int ou str")

    if len(siret_s) != 14 or not siret_s.isdigit():
        raise ValueError(f"Le siret {siret} doit être quatorze chiffres")
    siren_rs = str(siret_s)[0:9]

    if isinstance(siret, str):
        return siren_rs
    else:
        return int(siren_rs)
