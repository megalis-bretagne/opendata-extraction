from flask import current_app

from functools import lru_cache

from .ClientApiSirene import _ClientApiInseeStrategy,_ClientApiEntrepriseStrategy, ClientApiSirene
from .data_structures import Etablissement

@lru_cache(maxsize=25)
def etablissement_siege_pour_siren(siren: str) -> Etablissement:
    client_api_sirene = _get_client_api_sirene()
    return client_api_sirene.etablissement_siege_du_siren(siren)

@lru_cache(maxsize=25)
def etablissements_pour_siren(siren: str) -> list[Etablissement]:
    client_api_sirene = _get_client_api_sirene()
    return client_api_sirene.etablissements(siren)

def _get_client_api_sirene():
    use_api_insee = current_app.config['USE_API_INSEE']

    strategies = [_get_client_api_insee(), _get_client_api_entreprise()]
    if not use_api_insee:
        strategies.reverse()

    return ClientApiSirene(*strategies)
    
def _get_client_api_insee():
    key = current_app.config['API_SIREN_KEY']
    secret = current_app.config['API_SIREN_SECRET']
    return _ClientApiInseeStrategy(key, secret)

def _get_client_api_entreprise():
    url = current_app.config['URL_API_ENNTREPRISE']
    return _ClientApiEntrepriseStrategy(url)