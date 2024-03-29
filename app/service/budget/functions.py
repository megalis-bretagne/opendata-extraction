from pathlib import Path
from typing import Callable, Optional

from yatotem2scdl import EtapeBudgetaire, TotemBudgetMetadata, Options

from app.shared.totem_conversion_utils import make_or_get_budget_convertisseur
from app.shared.constants import PLANS_DE_COMPTES_PATH
from app.models.publication_model import Publication, Acte

from . import logger
from .datastructures import TotemMetadataTuple
from .prometheus import MAKE_SCDL_FILE_FROM_TOTEM, LISTE_TOTEM_METADATA_HISTOGRAM


def _get_or_make_scdl_from_totem(xml_fp: Path):
    scdl_path = xml_fp.with_suffix(".scdl")
    if scdl_path.exists():
        return scdl_path

    return _make_scdl_file_from_totem(xml_fp)


@MAKE_SCDL_FILE_FROM_TOTEM.time()
def _make_scdl_file_from_totem(xml_fp: Path):
    _convertisseur = make_or_get_budget_convertisseur()

    scdl_path = xml_fp.with_suffix(".scdl")
    assert xml_fp.is_file(), f"{xml_fp} doit pointer vers un fichier"

    if scdl_path.is_file():
        logger.info(f"On écrase le fichier SCDL existant: {scdl_path}")
    else:
        logger.info(f"On créee SCDL: {scdl_path}")

    with scdl_path.open("w") as f:
        _convertisseur.totem_budget_vers_scdl(
            xml_fp,
            PLANS_DE_COMPTES_PATH,
            f,
            Options(inclure_header_csv=False),
        )
    return scdl_path


@LISTE_TOTEM_METADATA_HISTOGRAM.time()
def _liste_totem_with_metadata(siren: str) -> list[TotemMetadataTuple]:
    """Liste les chemins des fichiers totems ainsi que leurs metadonnées associées"""

    def retrieve_metadata(xml_fp):
        convertisseur = make_or_get_budget_convertisseur()
        return convertisseur.totem_budget_metadata(xml_fp, PLANS_DE_COMPTES_PATH)

    publication_actes = (
        Publication.query
        # nature_acte = 5 => budget, etat=1 => est publié, date_budget lors des traitement des XML budget
        .filter(
            Publication.siren == siren,
            Publication.acte_nature == 5,
            Publication.etat == 1,
            Publication.date_budget != None,
            Publication.est_supprime == False,
        )
        .join(Acte, Acte.publication_id == Publication.id)
        .all()
    )
    # fmt: off
    totem_xml_filepaths = (
        Path(acte.path) 
        for p in publication_actes 
        for acte in p.actes
    )
    # fmt: on

    results: list[TotemMetadataTuple] = []
    for xml_fp in totem_xml_filepaths:
        metadata = retrieve_metadata(xml_fp)
        results.append(TotemMetadataTuple(xml_fp, metadata))

    return results


def _budget_metadata_predicate(
    annee: Optional[int] = None,
    siret: Optional[str] = None,
    etape: EtapeBudgetaire = None,
) -> Callable[[TotemBudgetMetadata], bool]:
    def predicate(metadata: TotemBudgetMetadata):
        _siret = int(siret) if siret is not None else siret

        if _siret and _siret != metadata.id_etablissement:
            logger.debug(
                f"On exclut {metadata} car {_siret} != {metadata.id_etablissement}"
            )
            return False
        if annee and annee != metadata.annee_exercice:
            logger.debug(
                f"On exclut {metadata} car {annee} != {metadata.annee_exercice}"
            )
            return False
        if etape and etape != metadata.etape_budgetaire:
            logger.debug(
                f"On exclut {metadata} car {etape} != {metadata.etape_budgetaire}"
            )
            return False

        return True

    return predicate
