import logging

from typing import Callable, Optional

from app.models.publication_model import Acte, Publication

from yatotem2scdl.conversion import EtapeBudgetaire, TotemBudgetMetadata

from pathlib import Path
from app.shared.constants import PLANS_DE_COMPTES_PATH
from app.shared.totem_conversion_utils import make_or_get_budget_convertisseur

from app.shared.client_api_sirene import Etablissement

from .data_structures import (
    GetBudgetMarqueBlancheApiResponse,
    GetInfoPlanDeComptesBudgetMarqueBlancheApi,
    InfoBudgetDisponiblesApi,
    InfosEtablissement,
    LigneBudgetMarqueBlancheApi,
    _TotemAndMetadata,
    RessourcesBudgetairesDisponibles,
)
from .exceptions import (
    _ImpossibleParserLigne,
    AucuneDonneeBudgetError,
    ImpossibleDexploiterBudgetError,
)

from .functions import (
    _etape_from_str,
    _api_sirene_etablissement_siege,
    _api_sirene_etablissements,
    _wrap_in_budget_marque_blanche_api_ex,
    _to_scdl_csv_reader,
    _extraire_pdc_unique,
    extraire_siren,
)

from ._ExtracteurInfoPdc import _ExtracteurInfoPdc


class BudgetMarqueBlancheApiService:
    def __init__(self):
        self.__logger = logging.getLogger(self.__class__.__name__)
        self.convertisseur = make_or_get_budget_convertisseur()

    @_wrap_in_budget_marque_blanche_api_ex
    def ressources_budgetaires_disponibles(
        self, siren: str
    ) -> InfoBudgetDisponiblesApi:

        self.__logger.info(
            f"Récupération des ressources budgetaires disponibles pour le siren {siren}"
        )

        all_totems_and_metadata = self._liste_totem_with_metadata(siren)
        ressources: RessourcesBudgetairesDisponibles = {}

        _lst_siret = []
        for totem_and_metadata in all_totems_and_metadata:
            metadata = totem_and_metadata.metadata
            annee = str(metadata.annee_exercice)
            siret = str(metadata.id_etablissement)
            etape = metadata.etape_budgetaire

            disp_annee = ressources.setdefault(annee, {})
            disp_nic = disp_annee.setdefault(siret, set())
            disp_nic.add(etape)
            _lst_siret.append(siret)

        infos_etablissements = self._extraire_infos_etab_siret(siren, _lst_siret)

        answer = InfoBudgetDisponiblesApi(
            str(siren),
            ressources,
            infos_etablissements,
        )
        return answer

    @_wrap_in_budget_marque_blanche_api_ex
    def retrieve_pdc_info(
        self,
        annee: int,
        siret: str,
    ):

        siren = str(extraire_siren(siret))

        self.__logger.info(
            f"Récupération du plan de compte pour le siret {siret} et l'année {annee}."
        )

        all_totems_and_metadata = self._liste_totem_with_metadata(siren)
        pred = self._budget_metadata_predicate(annee, siret)
        totems_and_metadata = [x for x in all_totems_and_metadata if pred(x.metadata)]

        ls_metadata = [x.metadata for x in totems_and_metadata]

        plan_de_comptes = _extraire_pdc_unique(ls_metadata)

        extracteur = _ExtracteurInfoPdc(plan_de_comptes)
        references_fonctionnelles = extracteur.extraire_references_fonctionnelles()
        comptes_nature = extracteur.extraire_comptes_nature()
        return GetInfoPlanDeComptesBudgetMarqueBlancheApi(
            references_fonctionnelles, comptes_nature
        )

    @_wrap_in_budget_marque_blanche_api_ex
    def retrieve_budget_info(
        self, annee: int, siret: str, etape_str: str
    ) -> GetBudgetMarqueBlancheApiResponse:

        etape = _etape_from_str(etape_str)
        siren = str(extraire_siren(siret))

        self.__logger.info(
            f"Récupération des données budgetaires pour le siret {siret}"
            f" l'année {annee} et l'étape {etape}"
        )

        all_totem_with_metadata = self._liste_totem_with_metadata(siren)
        pred = self._budget_metadata_predicate(annee, siret, etape)
        totems_and_metadata = [x for x in all_totem_with_metadata if pred(x.metadata)]

        if not totems_and_metadata:
            raise AucuneDonneeBudgetError()

        nb_documents_budgetaires = len(totems_and_metadata)
        msg = f"On retient {nb_documents_budgetaires} documents budgetaire pour la requête"
        self.__logger.info(msg)

        if EtapeBudgetaire.PRIMITIF == etape \
            or EtapeBudgetaire.COMPTE_ADMIN == etape \
            and nb_documents_budgetaires > 1:
            msg = f"On ne devrait avoir qu'un seul document pour l'étape budgetaire primitive."
            self.__logger.warning(msg)

        lignes: list[LigneBudgetMarqueBlancheApi] = []
        nb_ignorees: int = 0

        for (xml, _) in totems_and_metadata:
            reader = _to_scdl_csv_reader(self.convertisseur, xml)
            for _, row in enumerate(reader):
                try:
                    ligne = self._parse_ligne_scdl(row, etape)
                    if ligne:
                        lignes.append(ligne)
                    else:
                        nb_ignorees += 1
                except _ImpossibleParserLigne as err:
                    raise ImpossibleDexploiterBudgetError(xml, err.message)

        if nb_ignorees > 0:
            self.__logger.warning(
                f"{nb_ignorees} lignes ont été ignorées car elles ne respectent pas les attendus"
            )

        return GetBudgetMarqueBlancheApiResponse(
            etape=etape,
            annee=annee,
            siret=str(siret),
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
                self.__logger.warning(
                    f"La nature de la ligne budgétaire n'est pas renseignée."
                )

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

    def _retrieve_montant_de_ligne_scdl(
        self,
        ligne: dict[str, str],
        etape: EtapeBudgetaire,
    ) -> float:
        #
        # Chaque ligne de compte administratif
        # a un montant, BGT_MTREAL est parfois non renseigné.
        # Ce qui équivaut à un montant de 0
        #
        col_mtreal = ligne["BGT_MTREAL"]
        col_mtprev = ligne["BGT_MTPREV"]
        col_mtpropnouv = ligne["BGT_MTPROPNOUV"]

        if etape == EtapeBudgetaire.COMPTE_ADMIN:
            return float(col_mtreal) if col_mtreal else 0

        if etape == EtapeBudgetaire.PRIMITIF:
            if not col_mtprev:
                self.__logger.warn("Colonne MTPREV vide pour budget primitif")
                return 0
            return float(col_mtprev)
        
        if etape == EtapeBudgetaire.DECISION_MODIF:
            return float(col_mtpropnouv) if col_mtpropnouv else 0

        else:
            # XXX: On ne devrait pas reçevoir d'erreurs pour les autres étapes
            raise NotImplementedError("")

    def _extraire_infos_etab_siret(
        self, siren: str, sirets: list[str]
    ) -> dict[str, InfosEtablissement]:
        """Extraction des informations d'établissement pour les sirets"""

        etablissements = self._api_sirene_etablissements(siren)
        infos_etablissements = {
            e.siret: InfosEtablissement.from_api_sirene_etablissement(e)
            for e in etablissements
            if e.siret in sirets
        }
        return infos_etablissements

    def _liste_totem_with_metadata(
        self,
        siren: str,
    ) -> list[_TotemAndMetadata]:
        """Liste les chemins des fichiers totems ainsi que leurs metadonnées associées"""

        def retrieve_metadata(xml_fp):
            return self.convertisseur.totem_budget_metadata(
                xml_fp, PLANS_DE_COMPTES_PATH
            )

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

        results: list[_TotemAndMetadata] = []
        for xml_fp in totem_xml_filepaths:
            metadata = retrieve_metadata(xml_fp)
            results.append(_TotemAndMetadata(xml_fp, metadata))

        return results

    def _budget_metadata_predicate(
        self,
        annee: int,
        siret: str,
        etape: EtapeBudgetaire = None,
    ) -> Callable[[TotemBudgetMetadata], bool]:
        def predicate(metadata: TotemBudgetMetadata):
            _siret = int(siret) if siret is not None else siret

            if _siret and _siret != metadata.id_etablissement:
                self.__logger.debug(
                    f"On exclut {metadata} car {_siret} != {metadata.id_etablissement}"
                )
                return False
            if annee and annee != metadata.annee_exercice:
                self.__logger.debug(
                    f"On exclut {metadata} car {annee} != {metadata.annee_exercice}"
                )
                return False
            if etape and etape != metadata.etape_budgetaire:
                self.__logger.debug(
                    f"On exclut {metadata} car {etape} != {metadata.etape_budgetaire}"
                )
                return False

            return True

        return predicate

    def _api_sirene_etablissement_siege(self, siren: str) -> Etablissement:
        return _api_sirene_etablissement_siege(siren, self.__logger)

    def _api_sirene_etablissements(self, siren: str) -> list[Etablissement]:
        return _api_sirene_etablissements(siren, self.__logger)
