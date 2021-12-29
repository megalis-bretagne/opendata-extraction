import array
import json

import requests
from flask import current_app

from app.service.Singleton import Singleton


class OrganizationService(metaclass=Singleton):
    """ Service organisation pour udata megalis """
    ORGANIZATION_ENDPOINT = "/organizations/"

    def __init__(self):
        self.HEADERS = {
            'X-API-KEY': current_app.config['API_KEY_UDATA_MEGALIS']
        }
        self.API = current_app.config['API_UDATA_MEGALIS']

    def get(self, siren) -> dict or None:
        response = requests.get(self.API + self.ORGANIZATION_ENDPOINT, params={'q': 'siren : ' + siren},
                                headers=self.HEADERS)

        if response.status_code == 200:
            result = json.loads(response.content.decode("utf-8"))
            if result['total'] == 1:
                return result['data'][0]
        return None

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
