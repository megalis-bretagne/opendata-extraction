import json
import re
from typing import Union

import requests
from flask import current_app

from app.service.Singleton import Singleton

from .exceptions import ( 
    OrganisationNonUniqueError,
    OrganisationIntrouvableError,
    OrganisationUnexpectedApiStatusError,
    _wrap_get_organisation_errors,
)


class OrganizationService(metaclass=Singleton):
    """ Service organisation pour udata """
    ORGANIZATION_ENDPOINT = "/organizations/"

    def __init__(self):
        self.HEADERS = {
            'X-API-KEY': current_app.config['API_KEY_UDATA']
        }
        self.API = current_app.config['API_UDATA']

    @_wrap_get_organisation_errors
    def get(self, siren) -> dict:
        response = requests.get(self.API + "/2" + self.ORGANIZATION_ENDPOINT + "search/", params={'q': 'siren : ' + siren},
                                headers=self.HEADERS)

        status_code = response.status_code

        response.raise_for_status()

        if status_code == 200:
            result = json.loads(response.content.decode("utf-8"))
            nb_org = result['total']

            if nb_org > 1:
                raise OrganisationNonUniqueError(nb_org, siren)
            elif nb_org == 0:
                raise OrganisationIntrouvableError(siren)

            return result['data'][0]
        else:
            raise OrganisationUnexpectedApiStatusError(siren, status_code)

    def get_all_sirens(self) -> list:
        page_size = 50
        next_page = self.API + "/2" + self.ORGANIZATION_ENDPOINT + "search/" + "?q=siren+%3A&page_size={}&page={}".format(page_size, "1")
        sirens = []
        while next_page is not None:
            response = requests.get(next_page, headers=self.HEADERS)
            result = json.loads(response.content.decode("utf-8"))
            next_page = result['next_page']
            for organization in result['data']:
                search = re.search(r"siren : ([0-9]*)", organization['description'])
                assert search is not None
                siren = search.group(1)
                sirens.append(siren)

        return sirens

    def get_datasets(self, id_organization) -> Union[list, None]:

        response = requests.get(self.API + "/1" + self.ORGANIZATION_ENDPOINT + id_organization + '/datasets/',
                                headers=self.HEADERS)
        result = json.loads(response.content.decode("utf-8"))
        return result['data']

    def __get_dataset(self, id_organization, type_doc) -> Union[dict, None]:
        datasets = self.get_datasets(id_organization)
        if datasets is None:
            return None

        for dataset in datasets:
            if 'extraction:type' in dataset['extras'] and dataset['extras']['extraction:type'] == type_doc:
                return dataset

        return None

    def get_dataset_budget(self, id_organization) -> Union[dict, None]:
        return self.__get_dataset(id_organization, 'budget')

    def get_dataset_deliberation(self, id_organization) -> Union[dict, None]:
        return self.__get_dataset(id_organization, 'deliberation')

    def get_dataset_decp(self, id_organization) -> Union[dict, None]:
        return self.__get_dataset(id_organization, 'decp')
