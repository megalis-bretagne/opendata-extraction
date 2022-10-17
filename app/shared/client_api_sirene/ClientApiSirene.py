from abc import ABC, abstractmethod
from typing import Any, Callable
from urllib.error import HTTPError
from . import logger
from .data_structures import Etablissement
from .exceptions import ErreurClientApiSirene, SireneInvalide

from api_insee import ApiInsee

import requests


def _safeget(dct, *keys):
    for key in keys:

        if dct is None:
            return None

        try:
            dct = dct[key]
        except KeyError:
            return None

    return dct


def _wrap_ex_in_erreur_api_client_ex(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ErreurClientApiSirene as err:
            raise err
        except Exception as err:
            raise ErreurClientApiSirene() from err

    return inner


class _AbstractClientApiSireneStrategy(ABC):

    strategy_name: str

    @abstractmethod
    def etablissements(self, siren: str) -> list[Etablissement]:
        """Récupère les établissements relatifs au siren

        Args:
            siren (str): siren de l'unité légale

        Returns:
            list[Etablissement]: list d'information d'établissements
        """
        pass

    @abstractmethod
    def etablissement_siege_du_siren(self, siren: str) -> Etablissement:
        """Récupère l'établissement siège du siren donné

        Args:
            siren (str): siren de l'unité légale

        Raises:
            ErreurClientApiSirene: Erreur en cas d'établissement non trouvé ou d'echec de communication API

        Returns:
            Etablissement: informations de l'établissement siège
        """
        pass


class _ClientApiEntrepriseStrategy(_AbstractClientApiSireneStrategy):
    def __init__(self, url_api_entreprise: str) -> None:
        super().__init__()
        self.strategy_name = "API entreprise"
        self._url_api_entreprise = url_api_entreprise

    @_wrap_ex_in_erreur_api_client_ex
    def etablissements(self, siren: str) -> list[Etablissement]:
        logger.debug(f"Établissements du siren: {siren}")
        return self._etablissements(siren)

    @_wrap_ex_in_erreur_api_client_ex
    def etablissement_siege_du_siren(self, siren: str) -> Etablissement:
        logger.debug(f"Établissement siège du siren: {siren}")

        etablissements = self._etablissements(siren)
        sieges = [e for e in etablissements if e.est_siege]
        assert len(sieges) == 1
        return sieges[0]

    def _etablissements(self, siren: str) -> list[Etablissement]:
        url = self._make_url_unite_legale(siren)
        logger.debug(f"Appel à l'URL {url}")

        r = requests.get(url)
        if r.status_code == 404:
            raise SireneInvalide(siren)
        if r.status_code != 200:
            raise ErreurClientApiSirene(str(r))

        response = r.json()
        r_ul = _safeget(response, "unite_legale")
        r_ul_denomination = _safeget(r_ul, "denomination")
        r_etablissements = _safeget(r_ul, "etablissements")

        etablissements = [
            self._extract_etab(etab, r_ul_denomination) for etab in r_etablissements
        ]
        return etablissements

    def _extract_etab(self, r_etablissement, denomination) -> Etablissement:

        nic = _safeget(r_etablissement, "nic")
        siret = _safeget(r_etablissement, "siret")
        est_siege = _safeget(r_etablissement, "etablissement_siege") == "true"
        denomination_unite_legale = denomination
        enseigne = _safeget(r_etablissement, "enseigne_1")

        return Etablissement(
            nic=nic,
            siret=siret,
            denomination_unite_legale=denomination_unite_legale,
            est_siege=est_siege,
            enseigne=enseigne,
        )

    def _make_url_unite_legale(self, siren: str):
        return f"{self._url_api_entreprise}/unites_legales/{siren}"


class _ClientApiInseeStrategy(_AbstractClientApiSireneStrategy):
    def __init__(self, key: str, secret: str) -> None:
        super().__init__()
        self.strategy_name = "API INSEE"
        self._key = key
        self._secret = secret

    @_wrap_ex_in_erreur_api_client_ex
    def etablissements(self, siren: str) -> list[Etablissement]:
        logger.debug(f"Établissements du siren: {siren}")

        etablissements = self._etablissements(siren)
        return etablissements

    @_wrap_ex_in_erreur_api_client_ex
    def etablissement_siege_du_siren(self, siren: str) -> Etablissement:
        logger.debug(f"Établissement siège du siren: {siren}")

        etablissements = self._etablissements(siren, q={ "siren": siren, "etablissementSiege": True})
        sieges = [e for e in etablissements if e.est_siege]
        assert len(sieges) == 1
        return sieges[0]

    def _etablissements(self, siren: str, q=None) -> list[Etablissement]:
        api = ApiInsee(
            key=self._key,
            secret=self._secret,
        )

        if q is None:
            q = {"siren": siren}

        try:
            data = api.siret(q=q).get()
        except HTTPError as e:
            if e.status == 404:
                raise SireneInvalide(siren)
            raise

        if len(data["etablissements"]) <= 0:
            raise ErreurClientApiSirene(f"Aucun établissement associé au siren {siren}")

        etablissements = [self._extract_etab(e) for e in data["etablissements"]]
        return etablissements

    def _extract_etab(self, api_response_etab) -> Etablissement:

        r_etab = api_response_etab
        r_etab_ul = _safeget(r_etab, "uniteLegale")

        nic = _safeget(r_etab, "nic")
        siret = _safeget(r_etab, "siret")
        denomination_unite_legale = _safeget(r_etab_ul, "denominationUniteLegale")
        est_siege = _safeget(r_etab, "etablissementSiege")

        denomination_unite_legale = _safeget(r_etab_ul, "denominationUniteLegale")

        periodes = _safeget(r_etab, "periodesEtablissement")
        periode = periodes[0] if periodes else None
        enseigne = _safeget(periode, "enseigne1Etablissement")

        return Etablissement(
            nic=nic,
            siret=siret,
            denomination_unite_legale=denomination_unite_legale,
            est_siege=est_siege,
            enseigne=enseigne,
        )


class ClientApiSirene:
    """
    Client API sirene
    Peut prendre plusieurs strategies d'accès à l'API sirene
    et les utilise dans l'ordre jusqu'à ce qu'une fonctionne.
    """

    def __init__(self, *strategies) -> None:
        self.strategies = strategies

    def etablissements(self, siren: str) -> list[Etablissement]:
        return self._try_with_strategies(lambda strat: strat.etablissements(siren))

    def etablissement_siege_du_siren(self, siren: str) -> Etablissement:

        return self._try_with_strategies(
            lambda strat: strat.etablissement_siege_du_siren(siren)
        )

    def _try_with_strategies(
        self, call: Callable[[_AbstractClientApiSireneStrategy], Any]
    ) -> Any:
        for i, strategy in enumerate(self.strategies):
            try:
                strat_name = strategy.strategy_name
                logger.debug(f"Utilisation de la strategie: {strat_name}")
                return call(strategy)

            except ErreurClientApiSirene as err:
                error = err
                if i < len(self.strategies) - 1:
                    logger.warning(f"Erreur avec la strategie {strat_name}:")
                    logger.exception(err)
                    logger.warning(f"Essai d'une autre stratégie")
        raise error
