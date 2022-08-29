import logging

from typing import Optional

from app.models.publication_model import Acte, Publication

from yatotem2scdl.conversion import EtapeBudgetaire, TotemBudgetMetadata

from pathlib import Path
from app.shared.constants import PLANS_DE_COMPTES_PATH
from app.shared.totem_conversion_utils import make_or_get_budget_convertisseur

from .data_structures import (
    GetBudgetMarqueBlancheApiResponse,
    GetInfoPlanDeComptesBudgetMarqueBlancheApi,
    LigneBudgetMarqueBlancheApi,
    _TotemAndMetadata,
    _EtabInfo,
)
from .exceptions import (
    _ImpossibleParserLigne,
    AucuneDonneeBudgetError,
    ImpossibleDexploiterBudgetError,
)

from .functions import (
    _etape_from_str,
    _infos_etab,
    _wrap_in_budget_marque_blanche_api_ex,
    _to_scdl_csv_reader,
    extraire_siren,
    _extraire_pdc_unique
)

from ._ExtracteurInfoPdc import _ExtracteurInfoPdc


class BudgetMarqueBlancheApiService:
    def __init__(self):
        self.__logger = logging.getLogger(self.__class__.__name__)
        self.convertisseur = make_or_get_budget_convertisseur()

    @_wrap_in_budget_marque_blanche_api_ex
    def annees_disponibles(self, siren: int) -> list[str]:
        dates = (
            Publication.query.with_entities(Publication.date_budget)
            .filter_by(siren=siren)
            .distinct()
            .all()
        )
        answer = list(map(lambda s: s[0], dates))
        return answer
    
    @_wrap_in_budget_marque_blanche_api_ex
    def retrieve_pdc_info(
        self,
        siren: int,
        annee: int,
    ):
        (_, siret_siege) = self._infos_etab(str(siren))
        totems_and_metadata = self._liste_totem_with_metadata(
            siret_siege,
            annee,
        )
        ls_metadata = [x.metadata for x in totems_and_metadata]
        
        plan_de_comptes = _extraire_pdc_unique(ls_metadata)

        extracteur = _ExtracteurInfoPdc(plan_de_comptes)
        references_fonctionnelles = extracteur.extraire_references_fonctionnelles()
        comptes_nature = extracteur.extraire_comptes_nature()
        return GetInfoPlanDeComptesBudgetMarqueBlancheApi(references_fonctionnelles, comptes_nature)

    @_wrap_in_budget_marque_blanche_api_ex
    def retrieve_info_budget(
        self, 
        siren: int, annee: int,etape_str: str,
    ) -> GetBudgetMarqueBlancheApiResponse:

        etape = _etape_from_str(etape_str)
        (denomination, siret_siege) = self._infos_etab(str(siren))

        totems_and_metadata = self._liste_totem_with_metadata(
            siret_siege, 
            annee, 
            etape,
        )
        if not totems_and_metadata:
            raise AucuneDonneeBudgetError()

        msg = f"On retient {len(totems_and_metadata)} documents budgetaire pour la requête"
        self.__logger.info(msg)

        lignes: list[LigneBudgetMarqueBlancheApi] = []
        nb_ignorees: int = 0

        for (xml, _) in totems_and_metadata:
            reader = _to_scdl_csv_reader(self.convertisseur, xml)
            for _,row in enumerate(reader):
                try:
                    ligne = self._parse_ligne_scdl(row, etape)
                    if ligne:
                        lignes.append(ligne)
                    else:
                        nb_ignorees += 1
                except _ImpossibleParserLigne as err:
                    raise ImpossibleDexploiterBudgetError(xml, err.message)
        
        if nb_ignorees > 0:
            self.__logger.warning(f"{nb_ignorees} lignes ont été ignorées car elles ne respectent pas les attendus")

        return GetBudgetMarqueBlancheApiResponse(
            etape=etape,
            annee=annee,
            siren=str(siren),
            siret_siege=str(siret_siege),
            denomination_siege=denomination,
            lignes=lignes,
        )

    def _parse_ligne_scdl(
        self, 
        ligne: dict[str, str],
        etape: EtapeBudgetaire,
    ) -> Optional[LigneBudgetMarqueBlancheApi]:

        try:
            col_codrd = ligne["BGT_CODRD"]
            col_fonction = ligne["BGT_FONCTION"]

            col_nature = ligne["BGT_NATURE"]

            montant = self._retrieve_montant_de_ligne_scdl(ligne, etape)

            if not col_codrd:
                raise _ImpossibleParserLigne("Le SCDL contient un CODRD non renseigné")
            if not col_nature:
                self.__logger.warning(f"La nature de la ligne budgétaire n'est pas renseignée.")

            recette = col_codrd == "recette"

            return LigneBudgetMarqueBlancheApi(
                fonction_code=col_fonction,
                compte_nature_code=col_nature,
                recette=recette,
                montant=float(montant),
            )
        except _ImpossibleParserLigne as err:
            raise err
        except Exception as err:
            raise _ImpossibleParserLigne(str(err)) from err

    def _retrieve_montant_de_ligne_scdl(self, ligne: dict[str, str], etape: EtapeBudgetaire) -> float:
        #
        # Chaque ligne de compte administratif
        # a un montant, BGT_MTREAL est parfois non renseigné.
        # Ce qui équivaut à un montant de 0
        #
        col_mtreal = ligne["BGT_MTREAL"]
        if etape == EtapeBudgetaire.COMPTE_ADMIN:
            return float(col_mtreal) if col_mtreal else 0
        else:
            # TODO: récupération du montant pour les autres étapes
            raise NotImplementedError("")

    def _liste_totem_with_metadata(
        self, 
        siret: int, annee: int, 
        etape: EtapeBudgetaire = None,
    ) -> list[_TotemAndMetadata]:

        siret = int(siret)

        def retrieve_metadata(xml_fp):
            return self.convertisseur.totem_budget_metadata(
                xml_fp, PLANS_DE_COMPTES_PATH
            )

        def filter_out_totem(metadata: TotemBudgetMetadata):
            if siret != metadata.id_etablissement:
                self.__logger.info(
                    f"On exclut {xml_fp} puisque {siret} != {metadata.id_etablissement}"
                )
                return True
            if annee != metadata.annee_exercice:
                self.__logger.info(
                    f"On exclut {xml_fp} puisque {annee} != {metadata.annee_exercice}"
                )
                return True
            if etape and etape != metadata.etape_budgetaire:
                self.__logger.info(
                    f"On exclut {xml_fp} puisque {etape} != {metadata.etape_budgetaire}"
                )
                return True
            return False

        siren = extraire_siren(str(siret))

        #
        # Les publication de type budget (acte_nature=5)
        # ont un acte qui pointe vers le fichier totem.
        #
        publication_actes = (
            Publication.query
            # nature_acte = 5 => budget, etat=1 => est publié
            .filter_by(siren=siren, acte_nature=5, date_budget=annee, etat=1)
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

        results: list[_TotemAndMetadata] = []
        for xml_fp in totem_xml_filepaths:
            metadata = retrieve_metadata(xml_fp)
            if filter_out_totem(metadata):
                continue
            results.append(_TotemAndMetadata(xml_fp, metadata))

        return results

    def _infos_etab(self, siren: str) -> _EtabInfo:
        return _infos_etab(siren, self.__logger)
