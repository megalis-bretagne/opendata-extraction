import array
import json

import requests
from flask import current_app

from app.service.Singleton import Singleton
from app.tasks import get_or_create_workdir


class DatasetService(metaclass=Singleton):
    """ Service dataset pour udata megalis """

    DATASETS_ENDPOINT = "/datasets/"

    def __init__(self):
        self.HEADERS = {
            'X-API-KEY': current_app.config['API_KEY_UDATA_MEGALIS']
        }
        self.API = current_app.config['API_UDATA_MEGALIS']

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
        response = requests.post(self.API + self.DATASETS_ENDPOINT, headers=self.HEADERS, json=payload)
        if response.status_code != 201:
            return None
        else:
            return json.loads(response.content.decode("utf-8"))

    def create_dataset_budget(self, organization: dict):
        description = "Budgets - " + organization['name']
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
        description = "Délibérations - " + organization['name']
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

    def create_dataset_decpself(self, organization: dict):
        description = "Données essentielles - " + organization['name']
        title = "Données essentielles - " + organization['name']
        array_tags = [
            "decp",
            "marche",
            "marche-public",
            "marches-publics"
        ]
        return self.__create_dataset(organization['id'], description, title, 'decp', array_tags)

    def __add_resource(self, dataset: dict, filename: str, schema: dict):
        """ Ajout une resource sur le dataset. Maj si fichier déja présent sur la resource """

        if dataset is None:
            return None
        id_dataset = dataset['id']
        for resource in dataset['resources']:
            if resource['title'].casefold() == filename.casefold():
                # Maj resource
                id_resource = resource['id']
                url = self.API + self.DATASETS_ENDPOINT + '{}/resources/{}/upload/'.format(id_dataset, id_resource)
                response = requests.post(url, files={
                    'file': open(get_or_create_workdir() + filename, 'rb'),
                }, headers=self.HEADERS)
                if response.status_code != 200:
                    return None
                else:
                    return json.loads(response.content.decode("utf-8"))

        # Création ressource
        url = self.API + self.DATASETS_ENDPOINT + '{}/upload/'.format(id_dataset)
        response = requests.post(url, files={
            'file': open(get_or_create_workdir() + filename, 'rb'),
        }, headers=self.HEADERS)

        if response.status_code != 201:
            return None

        resource = json.loads(response.content.decode("utf-8"))

        # Mise à jour des métadonnées d’une ressource
        url = self.API + self.DATASETS_ENDPOINT + '{}/resources/{}/'.format(id_dataset, resource['id'])
        requests.put(url, json={
            'format': filename.split(".")[-1],
            'schema': schema,
        }, headers=self.HEADERS)

        if response.status_code != 201:
            return None
        else:
            return resource

    def add_resource_budget(self, dataset: dict, filename: str):
        return self.__add_resource(dataset, filename, {'name': 'scdl/budget', 'version': '0.8.1'})

    def add_resource_deliberation(self, dataset: dict, filename: str):
        return self.__add_resource(dataset, filename, {'name': 'scdl/deliberations'})

    def add_resource_decp(self, dataset: dict, filename: str):
        return self.__add_resource(dataset, filename, {'name': '139bercy/format-commande-publique'})
