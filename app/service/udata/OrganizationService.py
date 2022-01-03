import array
import json
import re

import requests
from flask import current_app

from app.service.Singleton import Singleton


class OrganizationService(metaclass=Singleton):
    """ Service organisation pour udata """
    ORGANIZATION_ENDPOINT = "/organizations/"

    def __init__(self):
        self.HEADERS = {
            'X-API-KEY': current_app.config['API_KEY_UDATA']
        }
        self.API = current_app.config['API_UDATA']

    def get(self, siren) -> dict or None:
        response = requests.get(self.API + self.ORGANIZATION_ENDPOINT, params={'q': 'siren : ' + siren},
                                headers=self.HEADERS)

        if response.status_code == 200:
            result = json.loads(response.content.decode("utf-8"))
            if result['total'] == 1:
                return result['data'][0]
        return None

    def get_all_sirens(self) -> array:
        page_size = 50
        next_page = self.API + self.ORGANIZATION_ENDPOINT + "?q=siren+%3A&page_size={}&page={}".format(page_size, "1")
        sirens = []
        while next_page is not None:
            response = requests.get(next_page, headers=self.HEADERS)
            result = json.loads(response.content.decode("utf-8"))
            next_page = result['next_page']
            for organization in result['data']:
                siren = re.search(r"siren : ([0-9]*)", organization['description']).group(1)
                sirens.append(siren)

        return sirens

    def get_datasets(self, id_organization) -> array or None:

        response = requests.get(self.API + self.ORGANIZATION_ENDPOINT + id_organization + '/datasets/',
                                headers=self.HEADERS)
        result = json.loads(response.content.decode("utf-8"))
        return result['data']

    def __get_dataset(self, id_organization, type_doc) -> dict or None:
        datasets = self.get_datasets(id_organization)
        if datasets is None:
            return None

        for dataset in datasets:
            if 'extraction:type' in dataset['extras'] and dataset['extras']['extraction:type'] == type_doc:
                return dataset

        return None

    def get_dataset_budget(self, id_organization) -> dict or None:
        return self.__get_dataset(id_organization, 'budget')

    def get_dataset_deliberation(self, id_organization) -> dict or None:
        return self.__get_dataset(id_organization, 'deliberation')

    def get_dataset_decp(self, id_organization) -> dict or None:
        return self.__get_dataset(id_organization, 'decp')
