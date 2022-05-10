import array
import json

import requests
from flask import current_app

from app.service.Singleton import Singleton
from app.tasks import get_or_create_workdir


class DatasetService(metaclass=Singleton):
    """ Service dataset pour udata """

    DATASETS_ENDPOINT = "/datasets/"

    def __init__(self):
        self.HEADERS = {
            'X-API-KEY': current_app.config['API_KEY_UDATA']
        }
        self.API = current_app.config['API_UDATA']

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

    def delete_resource(self, dataset: dict, filename: str):
        if dataset is None:
            return
        for resource in dataset['resources']:
            if resource['title'] == filename:
                requests.delete(
                    self.API + self.DATASETS_ENDPOINT + dataset['id'] + "/resources/" + resource['id'] + "/",
                    headers=self.HEADERS)
