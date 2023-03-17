import calendar
import json
from pathlib import Path
import time
from typing import Generator, Union
from xml.dom import minidom
from xml.etree import ElementTree

from contextlib import contextmanager

import requests

from app import celeryapp
from app.tasks.utils import *

import app.shared.workdir_utils as workdir_utils

celery = celeryapp.celery


class SDMException(Exception):
    pass


@celery.task(name='generation_marche', bind=True)
def generation_marche(self):
    # generation annee
    t = time.localtime()
    annee = time.strftime('%Y', t)
    reponse = generation_and_publication_decp_pour_annee(annee)
    if reponse['status'] == 'KO':
        raise SDMException(reponse['message'])
    return reponse


@celery.task(name='generation_marche_annee', bind=True)
def generation_marche_annee(self, annee):
    reponse = generation_and_publication_decp_pour_annee(annee)
    if reponse['status'] == 'KO':
        raise SDMException(reponse['message'])
    return reponse


@celery.task(name='generation_marche_histo', bind=True)
def generation_marche_histo(self):
    annee_debut = 2014
    # generation annee
    t = time.localtime()
    annee_courante = int(time.strftime('%Y', t))
    annee_a_generer = annee_debut
    while annee_courante >= annee_a_generer:
        generation_and_publication_decp_pour_annee(str(annee_a_generer))
        annee_a_generer += 1
    print("END " + str(annee_a_generer))

@contextmanager
def generated_decp(annee, siren) -> Generator[Union[Path, None], None, None]:
    with workdir_utils.temporary_workdir() as tmp_dir:
        tmp_path = Path(tmp_dir)
        decp_path = generation_decp(root_path=tmp_path, annee=annee, siren=siren)
        yield decp_path
    


def generation_decp(root_path: Path, annee, siren) -> Union[Path, None]:
    """Genère le fichier decp pour l'année et le siren donné

    Args:
        root_path (Path): chemin du dossier parent dans lequel sera stocké le fichier decp

    Returns:
        Path: Chemin complet de l'emplacement du XML
    """
    
    # """génération du fichier decp pour un siren & annee donne. Si renvoie None alors aucun fichier n'a été généré"""

    ANNEE = annee
    url_jeton_sdm = current_app.config['URL_JETON_SDM']
    try:
        response = requests.get(url_jeton_sdm)
        doc = minidom.parseString(response.text)
        jeton = doc.getElementsByTagName("ticket")[0].firstChild.data

        url_format_pivot = current_app.config['URL_API_DECP']
        reponse_export_pivot = requests.post(url_format_pivot, json={
            'token': jeton,
            'format': 'xml',
            'siren': str(siren),
            'date_notif_min': '01-01-' + str(ANNEE),
            'date_notif_max': '31-12-' + str(ANNEE)
        })

        if reponse_export_pivot.status_code != 200:
            return None
    except Exception:
        return None

    decp_filename = f"decp-{siren}{annee}.xml"
    decp_fullpath = Path(root_path) / decp_filename
    try:
        text_file = open(decp_fullpath, "w")
        text_file.write(reponse_export_pivot.text)
        text_file.close()

    except FileNotFoundError:
        return None

    return decp_fullpath


def generation_and_publication_decp_pour_annee(annee):
    workdir_utils.clear_persistent_workdir()

    ANNEE = str(annee)
    url_jeton_sdm = current_app.config['URL_JETON_SDM']
    API_KEY = current_app.config['API_KEY_DATAGOUV']
    DATASET = current_app.config['DATASET_MARCHE_DATAGOUV']
    HEADERS = {
        'X-API-KEY': API_KEY,
    }

    try:
        decp_xml_fullpath = workdir_utils.get_or_create_persistent_workdir() + 'decp-' + str(ANNEE) + '.xml'

        response = requests.get(url_jeton_sdm);
        doc = minidom.parseString(response.text)
        jeton = doc.getElementsByTagName("ticket")[0].firstChild.data

        url_format_pivot = current_app.config['URL_API_DECP']

        # generation annee
        t = time.localtime()
        ANNEE_EN_COURS = time.strftime('%Y', t)
        MOIS_EN_COURS = time.strftime('%m', t)

        xml_data = None
        month = 1
        while month <= 12:
            month_str = "{:02d}".format(month)
            max_day = calendar.monthrange(int(annee), month)[1]

            if int(annee) == int(ANNEE_EN_COURS) and (month > int(MOIS_EN_COURS)):
                break
            try:
                reponse_export_pivot = requests.post(url_format_pivot, json={
                    'token': jeton,
                    'format': 'xml',
                    'date_notif_min': '01-' + month_str + '-' + str(ANNEE),
                    'date_notif_max': str(max_day) + '-' + month_str + '-' + str(ANNEE)
                })
                if reponse_export_pivot.status_code != 200:
                    return {'status': 'KO', 'message': 'erreur lors de l\'appel SDM pour l\'annee {}'.format(annee)}
            except Exception:
                return {'status': 'KO', 'message': 'erreur lors de l\'appel SDM pour l\'annee {}'.format(annee)}
            data = ElementTree.fromstring(reponse_export_pivot.text)
            if xml_data is None:
                xml_data = data
            else:
                xml_data.extend(data)
            month = month + 1

        # Ecriture du fichier dans dossier workdir
        f = open(decp_xml_fullpath, 'w', encoding='utf-8')
        if xml_data is not None:
            xmlstr = ElementTree.tostring(xml_data, encoding='utf-8', method='xml')
            f.write(xmlstr.decode("utf-8"))
        f.close()

        # On recherche l'id de la ressource pour l'année dans la dataset de megalis 5f4f4f8910f4b55843deae51
        RESOURCE_UID = 0
        url = api_url('/datasets/{}'.format(DATASET))
        response = requests.get(url)
        if response.status_code == 200:
            dataset = json.loads(response.text)
            for resource in dataset['resources']:
                if str(ANNEE) in resource['title']:
                    RESOURCE_UID = resource['id']
                    break
            if RESOURCE_UID != 0:

                print('update resource id :' + RESOURCE_UID)

                url = api_url('/datasets/{}/resources/{}/upload/'.format(DATASET, RESOURCE_UID))
                requests.post(url, files={
                    'file': open(decp_xml_fullpath, 'rb'),
                }, headers=HEADERS)

            else:
                print('Creation de la resource annee ' + str(ANNEE))

                # Mise à jour ressource
                url = api_url('/datasets/{}/upload/'.format(DATASET))
                response = requests.post(url, files={
                    'file': open(decp_xml_fullpath, 'rb'),
                }, headers=HEADERS)

                response = json.loads(response.text)
                RESOURCE_UID = response['id']

                # #Mise à jour des métadonnées d’une ressource
                url = api_url('/datasets/{}/resources/{}/'.format(DATASET, RESOURCE_UID))
                response = requests.put(url, json={
                    'format': 'xml',
                    'schema': {'name': '139bercy/format-commande-publique'}

                }, headers=HEADERS)

    except Exception:
        return {'status': 'KO', 'message': 'erreur lors de l\'appel SDM pour l\'annee {}'.format(annee)}

    return {'status': 'OK', 'message': 'publication decp sur data.gouv', 'annee': str(ANNEE)}


def api_url(path):
    API = current_app.config['API_DATAGOUV']
    return API + path
