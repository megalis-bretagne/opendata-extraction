import logging

from typing import Optional

from app.shared.totem_conversion_utils import make_or_get_budget_convertisseur
from app.shared.performance import warn_when_time_above

from app.service.budget import (
    EtapeBudgetaire, Totems,
)

from app.shared.client_api_sirene import Etablissement

from .budgets_data_structures import (
    GetBudgetMarqueBlancheApiResponse,
    InfoBudgetDisponiblesApi,
    InfosEtablissement,
    LigneBudgetMarqueBlancheApi,
    RessourcesBudgetairesDisponibles,
)
from .budgets_exceptions import (
    _ImpossibleParserLigne,
    AucuneDonneeBudgetError,
    ImpossibleDexploiterBudgetError,
)

from .budgets_functions import (
    _etape_from_str,
    _api_sirene_etablissement_siege,
    _api_sirene_etablissements,
    _wrap_in_budget_marque_blanche_api_ex,
    _prune_montant_a_zero,
    extraire_siren,
    pdc_path_to_api_response,
)


class BudgetsApiService:
    def __init__(self):
        self.__logger = logging.getLogger(self.__class__.__name__)
        self.convertisseur = make_or_get_budget_convertisseur()

    @warn_when_time_above(5)
    @_wrap_in_budget_marque_blanche_api_ex
    def ressources_budgetaires_disponibles(
        self, siren: str
    ) -> InfoBudgetDisponiblesApi:

        self.__logger.info(
            f"Récupération des ressources budgetaires disponibles pour le siren {siren}"
        )

        infos_etablissements = self._extraire_infos_etab_siret(siren)
        _infos_etab_sirets = {siret for siret in infos_etablissements.keys()}

        all_totems_and_metadata = Totems(siren).request().liste
        ressources: RessourcesBudgetairesDisponibles = {}

        _resources_sirets = set()
        for totem_and_metadata in all_totems_and_metadata:
            metadata = totem_and_metadata.metadata
            annee = str(metadata.annee_exercice)
            siret = str(metadata.id_etablissement)
            etape = metadata.etape_budgetaire

            if not siret in _infos_etab_sirets:
                self.__logger.debug(
                    f"Des données budgetaires existent pour le siret {siret} "
                    f"mais aucune données concernant l'établissement (probablement non diffusible), "
                    f"nous ne remontons donc pas les données budgetaires."
                )
                continue

            disp_annee = ressources.setdefault(annee, {})
            disp_nic = disp_annee.setdefault(siret, set())
            disp_nic.add(etape)
            _resources_sirets.add(siret)

        to_remove = _infos_etab_sirets.difference(_resources_sirets)
        for siret in to_remove:
            del infos_etablissements[siret]

        if len(ressources) == 0:
            raise AucuneDonneeBudgetError()

        answer = InfoBudgetDisponiblesApi(
            str(siren),
            ressources,
            infos_etablissements,
        )
        return answer

    @warn_when_time_above(5)
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

        totems = Totems(siren).annee(annee).siret(siret).request()
        totems.ensure_has_unique_pdc()
        plan_de_comptes = totems.first_pdc

        answer = pdc_path_to_api_response(plan_de_comptes)
        return answer

    @warn_when_time_above(5)
    @_wrap_in_budget_marque_blanche_api_ex
    @_prune_montant_a_zero
    def retrieve_budget_info(
        self, annee: int, siret: str, etape_str: str
    ) -> GetBudgetMarqueBlancheApiResponse:

        etape = _etape_from_str(etape_str)
        siren = str(extraire_siren(siret))

        self.__logger.info(
            f"Récupération des données budgetaires pour le siret {siret}"
            f" l'année {annee} et l'étape {etape}"
        )

        totems = Totems(siren).annee(annee).siret(siret).etape(etape).request()

        if not totems.liste:
            raise AucuneDonneeBudgetError()

        nb_documents_budgetaires = len(totems.liste)
        msg = f"On retient {nb_documents_budgetaires} documents budgetaire pour la requête"
        self.__logger.info(msg)

        if (
            EtapeBudgetaire.PRIMITIF == etape or EtapeBudgetaire.COMPTE_ADMIN == etape
        ) and nb_documents_budgetaires > 1:
            msg = f"On ne devrait avoir qu'un seul document pour {annee}, {siret}, {etape_str}"
            self.__logger.warning(msg)

        lignes: list[LigneBudgetMarqueBlancheApi] = []
        nb_ignorees: int = 0

        for row in totems.vers_scdl_rows():
            try:
                ligne = self._parse_ligne_scdl(row, etape)
                if ligne:
                    lignes.append(ligne)
                else:
                    nb_ignorees += 1
            except _ImpossibleParserLigne as err:
                raise ImpossibleDexploiterBudgetError(err.message)

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
        col_mtrarprec = ligne["BGT_MTRARPREC"]

        if etape == EtapeBudgetaire.COMPTE_ADMIN:
            return float(col_mtreal) if col_mtreal else 0

        if etape == EtapeBudgetaire.PRIMITIF:
            if not col_mtprev:
                self.__logger.warn("Colonne MTPREV vide pour budget primitif")
                return 0
            return float(col_mtprev)

        if etape == EtapeBudgetaire.DECISION_MODIF:
            propnouv = float(col_mtpropnouv) if col_mtpropnouv else 0
            mtrarprec = float(col_mtrarprec) if col_mtrarprec else 0
            return propnouv + mtrarprec

        else:
            # XXX: On ne devrait pas reçevoir d'erreurs pour les autres étapes
            raise NotImplementedError("")

    def _extraire_infos_etab_siret(self, siren: str) -> dict[str, InfosEtablissement]:
        """Extraction des informations d'établissement pour les sirets"""

        etablissements = self._api_sirene_etablissements(siren)
        infos_etablissements = {
            e.siret: InfosEtablissement.from_api_sirene_etablissement(e)
            for e in etablissements
        }
        return infos_etablissements

    def _api_sirene_etablissement_siege(self, siren: str) -> Etablissement:
        return _api_sirene_etablissement_siege(siren, self.__logger)

    def _api_sirene_etablissements(self, siren: str) -> list[Etablissement]:
        return _api_sirene_etablissements(siren, self.__logger)
