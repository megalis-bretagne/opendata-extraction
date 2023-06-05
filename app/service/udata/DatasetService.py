import array
import json
import logging
from pathlib import Path

import requests
from flask import current_app

from app.service.Singleton import Singleton

class DatasetServiceException(Exception):
    pass
class AddResourceUrlException(DatasetServiceException):
    """Lors de l'echec de l'ajout/update d'une resource url"""
    pass

class DatasetService(metaclass=Singleton):
    """ Service dataset pour udata """

    DATASETS_ENDPOINT = "/datasets/"

    def __init__(self):
        self.__logger = logging.getLogger(__name__)
        catalogue_regionnal = current_app.config["CATALOGUE_REGIONAL"]
        self.HEADERS = {
            'X-API-KEY': catalogue_regionnal['API_KEY']
        }
        self.API = catalogue_regionnal['API_URL']

    def __do_title_matches(self, title: str, candidate: str):
        return title.casefold() == candidate.casefold()

    def __create_dataset(self, id_organization: str, description: str, title: str, type_extraction: str,
                         array_tags: array) -> dict or None:
        """ Création dataset sur id_organization."""
        payload = {
            "description": description,
            "extras": {
                "extraction:type": type_extraction
            },
            "frequency": "daily",
            "license": "lov2",
            "organization": {
                "id": id_organization
            },
            "tags": array_tags,
            "title": title
        }
        response = requests.post(self.API + "/1" + self.DATASETS_ENDPOINT, headers=self.HEADERS, json=payload)
        if response.status_code != 201:
            return None
        else:
            return json.loads(response.content.decode("utf-8"))

    def create_dataset_budget(self, organization: dict):
        description = "Ce jeu de données permet de répondre aux obligations réglementaires concernant la publication " \
                      "des données budgets des organismes adhérents de Mégalis Bretagne. Il permet également, " \
                      "en toute transparence d'informer les citoyens sur les décisions prises. Les données seront, " \
                      "à termes, récupérées automatiquement des flux transitant par le service de télétransmission " \
                      "des actes (par où passent les budgets des collectivités) de la plateforme de services Mégalis. " \
                      "Les données sont structurées au format SCDL et respecte donc le schéma national (" \
                      "https://schema.data.gouv.fr/scdl/budget/). Les données de l'année en cours sont mises à jour " \
                      "quotidiennement de façon automatique."
        title = "Budgets - " + organization['name']
        array_tags = [
            "budget",
            "budget-principal",
            "budgets",
            "budgets-annexes",
            "collectivite",
            "collectivites"
        ]
        return self.__create_dataset(organization['id'], description, title, 'budget', array_tags)

    def create_dataset_deliberation(self, organization: dict):
        description = "Ce jeu de données permet de répondre aux obligations réglementaires concernant la publication " \
                      "des données délibérations des organismes adhérents de Mégalis Bretagne. Il permet également, " \
                      "en toute transparence d'informer les citoyens sur les décisions prises. La dimension " \
                      "conformité au RGPD a également été prise en compte : les organismes peuvent choisir de publier " \
                      "la délibération (URL présente dans le schéma) ou de ne pas publier la délibération en tant que " \
                      "telle (tous les champs renseignés sauf l'URL de téléchargement de la délibération). Le fait de " \
                      "publier ou non les informations reste du ressort et de la responsabilité de chaque organisme. " \
                      "Techniquement, les données sont récupérées automatiquement des flux transitant par le service " \
                      "de télétransmission des actes (par où passent les délibérations des collectivités) de la " \
                      "plateforme de services Mégalis. Les données sont structurées au format SCDL (" \
                      "https://schema.data.gouv.fr/scdl/deliberations/). Les données de l'année en cours sont" \
                      "mises à jour quotidiennement de façon automatique. "

        title = "Délibérations - " + organization['name']
        array_tags = [
            "acte",
            "actes",
            "collectivite",
            "collectivites",
            "deliberation",
            "deliberations"
        ]
        return self.__create_dataset(organization['id'], description, title, 'deliberation', array_tags)

    def create_dataset_decp(self, organization: dict):
        description = "Ce jeu de données permet de répondre aux obligations réglementaires concernant la publication " \
                      "des données essentielles des marchés publics notifiés par Mégalis Bretagne (en cours " \
                      "d'exécution ou terminés). Il est issu d'une API de la salle des Marchés de Mégalis sur la base " \
                      "du format pivot. Il respecte le schéma national des données (" \
                      "https://github.com/139bercy/format-commande-publique). Il comprend toutes les données " \
                      "essentielles des organismes adhérents au service de la salle des marchés publics et ayant " \
                      "renseigné l'étape \"décision\" (attribution du marché) sur la salle des marchés publics de " \
                      "Mégalis Bretagne. Les données de l'année en cours sont mises à jour quotidiennement de façon " \
                      "automatique. "
        title = "Données essentielles - " + organization['name']
        array_tags = [
            "decp",
            "marche",
            "marche-public",
            "marches-publics"
        ]
        return self.__create_dataset(organization['id'], description, title, 'decp', array_tags)

    def __add_resource_url(self, *args, **kwargs):
        """Ajout d'une ressource sur le dataset en tant qu'url. Maj ou supprime/creation si les titres sont équivalents.
        raises:
            AddResourceUrlException
        """
        try:
            self.__add_resource_url_raw(*args, **kwargs)
        except AddResourceUrlException as e:
            raise
        except Exception as e:
            raise AddResourceUrlException(str(e)) from e

    def __add_resource_url_raw(self, dataset: dict, titre: str, url: str, schema: dict, format: str, mime: str):

        if dataset is None:
            raise AddResourceUrlException("Aucun dataset de fourni")
        id_dataset = dataset['id']
        resource_endpoint = self.API + "/1" + self.DATASETS_ENDPOINT + f"{id_dataset}/resources"

        desc = {
            'title': titre,
            'format': format,
            'mime': mime,
            'schema': schema,
            'url': url,
            'filetype': 'remote',
        }

        id_dataset = dataset['id']

        resources_similaires = [resource for resource in dataset['resources'] if self.__do_title_matches(resource['title'], candidate=titre)]
        if len(resources_similaires) > 1:
            self.__logger.warning(f"Plusieurs ressources avec le même titre ({titre}) pour le dataset {id_dataset}")
        
        # Cas d'un update de ressource
        for resource in resources_similaires:
            id = resource['id']
            desc['id'] = id
            endpoint = f"{resource_endpoint}/{id}"

            if resource['filetype'] == 'remote':
                response = requests.put(endpoint, json=desc, headers=self.HEADERS)
                response.raise_for_status()
                return json.loads(response.content.decode("utf-8"))
            else:
                self.__logger.warning(
                    f"La ressource {endpoint} n'est pas une ressource distance. "
                    "On supprime et recrée la ressource."
                )
                response = requests.delete(endpoint, headers=self.HEADERS) 
                response.raise_for_status()
                break # XXX: seulement le premier

        # Creation
        response_creation = requests.post(resource_endpoint, json=desc, headers=self.HEADERS)
        response_creation.raise_for_status()

        return json.loads(response_creation.content.decode("utf-8"))

    def __add_resource_fp(self, dataset: dict, filepath: Path, schema: dict):
        """ Ajout une resource sur le dataset. Maj si fichier déja présent sur la resource """

        file_name = filepath.name

        if dataset is None:
            return None
        id_dataset = dataset['id']
        for resource in dataset['resources']:
            if self.__do_title_matches(resource['title'], candidate=file_name):
                # Maj resource
                id_resource = resource['id']
                url = self.API + "/1" + self.DATASETS_ENDPOINT + '{}/resources/{}/upload/'.format(id_dataset, id_resource)
                response = requests.post(url, files={
                    'file': open(filepath, 'rb'),
                }, headers=self.HEADERS)
                if response.status_code != 200:
                    return None
                else:
                    return json.loads(response.content.decode("utf-8"))

        # Création ressource
        url = self.API + "/1" + self.DATASETS_ENDPOINT + '{}/upload/'.format(id_dataset)
        response = requests.post(url, files={
            'file': open(filepath, 'rb'),
        }, headers=self.HEADERS)

        if response.status_code != 201:
            return None

        resource = json.loads(response.content.decode("utf-8"))

        # Mise à jour des métadonnées d’une ressource
        url = self.API + "/1" + self.DATASETS_ENDPOINT + '{}/resources/{}/'.format(id_dataset, resource['id'])
        requests.put(url, json={
            'format': file_name.split(".")[-1],
            'schema': schema,
        }, headers=self.HEADERS)

        if response.status_code != 201:
            return None
        else:
            return resource

    def add_resource_budget_url(self, dataset: dict, titre: str, url: str):
        """
        Raises:
            AddResourceUrlException
        """
        return self.__add_resource_url(
            dataset = dataset, 
            titre=titre,
            url=url, 
            schema={'name': 'scdl/budget', 'version': '0.8.1'}, 
            format='csv', mime = 'text/csv',
        )
    
    def add_resource_deliberation_url(self, dataset: dict, titre: str, url: str):
        """
        Raises:
            AddResourceUrlException
        """
        return self.__add_resource_url(
            dataset=dataset,
            titre=titre,
            url=url,
            schema={'name': 'scdl/deliberations'},
            format='csv', mime = 'text/csv',
        )

    def add_resource_decp_url(self, dataset: dict, titre: str, url: str):
        """
        Raises:
            AddResourceUrlException
        """
        return self.__add_resource_url(
            dataset=dataset,
            titre=titre,
            url=url,
            schema={'name': '139bercy/format-commande-publique'},
            format='xml', mime = 'text/xml',
        )

    def add_resource_budget(self, dataset: dict, file_path: Path):
        return self.__add_resource_fp(dataset, file_path, {'name': 'scdl/budget', 'version': '0.8.1'})

    def add_resource_deliberation(self, dataset: dict, file_path: Path):
        return self.__add_resource_fp(dataset, file_path, {'name': 'scdl/deliberations'})

    def add_resource_decp(self, dataset: dict, file_path: Path):
        return self.__add_resource_fp(dataset, file_path, {'name': '139bercy/format-commande-publique'})

    def delete_resource_from_fp(self, dataset: dict, file_path: Path):
        file_name = file_path.name
        self.__delete_resource(dataset=dataset, titre=file_name)
    
    def delete_resource_with_title(self, dataset: dict, title: str):
        return self.__delete_resource(dataset=dataset, titre=title)

    def __delete_resource(self, dataset: dict, titre: str):
        if dataset is None:
            return
        for resource in dataset['resources']:
            if self.__do_title_matches(resource['title'], candidate=titre):
                requests.delete(
                    self.API + "/1" + self.DATASETS_ENDPOINT + dataset['id'] + "/resources/" + resource['id'] + "/",
                    headers=self.HEADERS)
