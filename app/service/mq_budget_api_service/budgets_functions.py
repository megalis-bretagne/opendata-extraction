import io
import csv
import logging
from pathlib import Path
from typing import Callable, Union

from .budgets_data_structures import EtapeBudgetaire, GetBudgetMarqueBlancheApiResponse, LigneBudgetMarqueBlancheApi

from app.shared.client_api_sirene import Etablissement

from .budgets_exceptions import (
    BudgetMarqueBlancheApiException,
    EtapeInvalideError,
    ImpossibleDextraireEtabInfoError,
)

from yatotem2scdl import (
    TotemBudgetMetadata,
    ConvertisseurTotemBudget, Options,
    EtapeBudgetaireInconnueErreur
)

from app.shared.constants import PLANS_DE_COMPTES_PATH


def _etape_from_str(etape: str) -> EtapeBudgetaire:
    try:
        return EtapeBudgetaire.from_str(etape)
    except EtapeBudgetaireInconnueErreur as err:
        raise EtapeInvalideError(etape) from err


def _to_scdl_csv_reader(convertisseur: ConvertisseurTotemBudget, xml_fp: Path):
    def _read_scdl_as_str(xml_fp: Path):
        scdl = ""
        with io.StringIO() as string_io:
            convertisseur.totem_budget_vers_scdl(
                xml_fp,
                PLANS_DE_COMPTES_PATH,
                string_io,
                Options(inclure_header_csv=False),
            )
            scdl = string_io.getvalue()
        return scdl

    entetes_seq = convertisseur.budget_scdl_entetes().split(",")
    scdl = _read_scdl_as_str(xml_fp)
    return csv.DictReader(scdl.splitlines(), entetes_seq)

def _extraire_pdc_unique(ls_totem_metadata: list[TotemBudgetMetadata]):
    pdc = { metadata.plan_de_compte for metadata in ls_totem_metadata }
    assert len(pdc) <= 1, "On ne devrait retrouver qu'un seul plan de compte pour ces informations budget"
    return pdc.pop()

def _api_sirene_etablissement_siege(siren: str, logger: logging.Logger) -> Etablissement:

    from app.shared.client_api_sirene.flask_functions import etablissement_siege_pour_siren

    try:
        etablissement = etablissement_siege_pour_siren(siren)
        logger.debug(f"Voici l'établissement {etablissement}")
        return etablissement

    except Exception as err:
        raise ImpossibleDextraireEtabInfoError(siren) from err

def _api_sirene_etablissements(siren: str, logger: logging.Logger) -> list[Etablissement]:

    from app.shared.client_api_sirene.flask_functions import etablissements_pour_siren

    try:
        etablissements = etablissements_pour_siren(siren)
        logger.debug(f"Voici les établissements pour le siren {etablissements}")
        return etablissements

    except Exception as err:
        raise ImpossibleDextraireEtabInfoError(siren) from err

def _wrap_in_budget_marque_blanche_api_ex(func):
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
