import json
import logging
from pathlib import Path
import tempfile
import time
from typing import Optional
import urllib.parse

import requests
from flask import current_app

from app import celeryapp
from app.models.parametrage_model import Parametrage
from app.models.publication_model import Publication
from app.tasks import solr_connexion, clear_wordir, get_or_create_workdir

from app.shared.constants import PLANS_DE_COMPTES_PATH
from app.shared.totem_conversion_utils import make_or_get_budget_convertisseur
from yatotem2scdl.conversion import Options

celery = celeryapp.celery


@celery.task(name='generation_and_publication_SCDL')
def generation_and_publication_scdl(type, param_annee):
    t = time.localtime()
    annee = time.strftime('%Y', t)

    if param_annee is not None and len(param_annee) > 1 and 2014 <= int(param_annee) <= 2050:
        annee = param_annee

    if type == '1':
        filename = generation_deliberation("*", annee, 'opendata_active')
        publication_datagouv_scdl(annee, get_or_create_workdir() + filename, type)
    elif type == '5':
        _genere_budget_et_publie_datagouv("*", annee, 'opendata_active')

    return {'status': 'OK', 'message': 'generation et publication scdl', 'annee': str(annee), 'type': str(type)}

def _genere_budget_et_publie_datagouv(siren: str, annee: str, flag_active: str):

    workdir = get_or_create_workdir()

    with tempfile.TemporaryDirectory(dir = workdir) as tmp_dir:
        csv_filepath = generation_budget(
            Path(tmp_dir), 
            siren, annee, flag_active)
        publication_datagouv_scdl(annee, csv_filepath, '5')

def generation_budget(root_dir: Path, siren, annee, flag_active=None) -> Path:

    annee = str(annee)
    siren = str(siren)
    type = '5'

    solr = solr_connexion()
    query = _solr_request_pour_budget(type, annee, siren, flag_active)
    query_params = {
        "fl": "siren,documentidentifier,classification_code,classification_nom,description,"
        "filepath,documenttype,date,est_publie,date_budget,publication_id",
    }

    csv_filename = (
        f"BUDGET-{annee}.csv" if siren == "*" else f"BUDGET-{siren}-{annee}.csv"
    )
    csv_filepath = Path(root_dir) / csv_filename
    convertisseur = make_or_get_budget_convertisseur()
    with open(csv_filepath, 'a', newline='') as csv_file:
        entetes = convertisseur.budget_scdl_entetes()
        csv_file.write(entetes + "\n")

        for doc_res in solr.search(q=query, sort="publication_id DESC,id ASC", cursorMark="*", **query_params):
            url = str(doc_res['filepath'][0])
            try:
                # on récupère la publication à publier en BDD
                publication = Publication.query.filter(Publication.id == doc_res['publication_id']).one()
                for acte in publication.actes:
                    options = Options(inclure_header_csv=False, lineterminator='\n')
                    convertisseur.totem_budget_vers_scdl(acte.path, PLANS_DE_COMPTES_PATH, output=csv_file, options=options)
            except Exception:
                logging.exception(f"Fichier ignoré: {url}")
    return csv_filepath

def _solr_request_pour_budget(type: str, annee: str, siren: str, flag_active: Optional[str]) -> str:
    query = f"typology: 99_BU AND est_publie: True AND documenttype: {type} AND date_budget: {annee}"
    if siren != "*":
        query = f"{query} AND siren: {siren}"
    if flag_active is not None:
        query = f"{query} AND {flag_active} : True"
    return query

def generation_acte(siren, annee):
    # on clear le workdir
    clear_wordir()
    ANNEE = str(annee)
    SIREN = str(siren)

    # connexion solr
    solr = solr_connexion()
    start = 0
    rows = 500

    # construction de la requete solr
    query = '-typology: PJ AND est_publie: true'
    if str(siren) == '*':
        filename = 'ACTES-' + ANNEE + '.csv'
    else:
        filename = 'ACTES-' + SIREN + '-' + ANNEE + '.csv'
        query = query + ' AND siren: ' + SIREN

    # generation de l'url du fichier scdl
    csv_file_path = get_or_create_workdir() + filename

    # On recherche dans apache solr les documents pour un publie qui ne sont pas des annexes et on fitre sur l'année passée en parametre ANNEE et le siren si present
    result = \
        solr.search(q=query,
                    **{
                        'fl': 'siren,documentidentifier,classification_code,classification_nom,description,'
                              'filepath,documenttype,date,est_publie,date_de_publication,documenttype',
                        'start': start,
                        'rows': rows,
                        'fq': 'date:[' + ANNEE + '-01-01T00:00:00Z TO ' + ANNEE + '-12-31T23:59:59Z]'
                    })

    lignes = []
    while len(result.docs) > 0:
        for doc_res in result.docs:
            parametrage = Parametrage.query.filter(Parametrage.siren == doc_res['siren']).first()
            COLL_NOM = parametrage.denomination
            DELIB_DATE = str(doc_res['date'][0].split("T", 1)[0])
            DELIB_ID = str(doc_res['documentidentifier'][0])
            DELIB_OBJET = str(doc_res['description'][0])
            COLL_SIRET = str(doc_res['siren'].zfill(9) + parametrage.nic)
            DELIB_MATIERE_CODE = str(doc_res['classification_code'])
            DELIB_MATIERE_NOM = str(doc_res['classification_nom'])

            PUBLICATION_DATE=str(doc_res['date_de_publication'][0].split("T", 1)[0])
            NATURE_ACTE = str(doc_res['documenttype'][0])

            BUDGET_ANNEE = ''
            BUDGET_NOM = ''
            PREF_ID = ''
            PREF_DATE = ''
            VOTE_EFFECTIF = ''
            VOTE_REEL = ''
            VOTE_POUR = ''
            VOTE_CONTRE = ''
            VOTE_ABSTENTION = ''
            if doc_res['est_publie'][0]:
                DELIB_URL = urllib.parse.quote(str(doc_res['filepath'][0]),safe="https://")
            else:
                DELIB_URL = ''

            line = '"' + COLL_NOM + '"' + ';' + '"' + COLL_SIRET + '"' + ';' + '"' + DELIB_ID + '"' + ';' + '"' + DELIB_DATE + '"' + ';' + '"' + DELIB_MATIERE_CODE + '"' + ';' \
                   + '"' + DELIB_MATIERE_NOM + '"' + ';' + '"' + DELIB_OBJET + '"' + ';' + '"' + BUDGET_ANNEE + '"' + ';' + '"' + BUDGET_NOM + '"' + ';' + '"' + PREF_ID + '"' + \
                   ';' + '"' + PREF_DATE + '"' + ';' + '"' + VOTE_EFFECTIF + '"' + ';' + '"' + VOTE_REEL + '"' + ';' + '"' + VOTE_POUR + '"' + ';' + '"' + VOTE_CONTRE + '"' + ';' \
                   + '"' + VOTE_ABSTENTION + '"' + ';' + '"' + DELIB_URL + '"' + ';' +  PUBLICATION_DATE + '"' + ';' + NATURE_ACTE + '"' +'\n'
            lignes.append(line)
        start = start + rows
        result = \
            solr.search(q=query,
                        **{
                            'fl': 'siren,documentidentifier,classification_code,classification_nom,description,'
                                  'filepath,documenttype,date,est_publie,date_de_publication,documenttype',
                            'start': start,
                            'rows': rows,
                            'fq': 'date:[' + ANNEE + '-01-01T00:00:00Z TO ' + ANNEE + '-12-31T23:59:59Z]'
                        })

    # Ecriture du fichier scdl
    header = "COLL_NOM;COLL_SIRET;DELIB_ID;DELIB_DATE;DELIB_MATIERE_CODE;DELIB_MATIERE_NOM;DELIB_OBJET;BUDGET_ANNEE;BUDGET_NOM;PREF_ID;PREF_DATE;VOTE_EFFECTIF;VOTE_REEL;VOTE_POUR;VOTE_CONTRE;VOTE_ABSTENTION;DELIB_URL;PUBLICATION_DATE;NATURE_ACTE"
    f = open(csv_file_path, 'w')
    f.write(header + '\n')
    for ligne in lignes:
        try:
            f.write(ligne)
        except Exception:
            logging.exception("on ignore la ligne" + ligne)
    f.close()
    return filename



def generation_deliberation(siren, annee, flag_active=None):
    # on clear le workdir
    clear_wordir()
    ANNEE = str(annee)
    SIREN = str(siren)

    TYPE = '1'
    # connexion solr
    solr = solr_connexion()

    start = 0
    rows = 500

    # construction de la requete solr
    query = 'typology: 99_DE AND documenttype:' + str(TYPE)
    if str(siren) == '*':
        filename = 'DELIBERATION-' + ANNEE + '.csv'
    else:
        filename = 'DELIBERATION-' + SIREN + '-' + ANNEE + '.csv'
        query = query + ' AND siren: ' + SIREN

    if flag_active is not None:
        query = query + ' AND ' + flag_active + ': True '

    # generation de l'url du fichier scdl
    csv_file_path = get_or_create_workdir() + filename

    # On recherche dans apache solr les documents pour un SIREN et un TYPE (deliberation, budget ...) et on fitre sur l'année passée en parametre ANNEE
    result = \
        solr.search(q=query,
                    **{
                        'fl': 'siren,documentidentifier,classification_code,classification_nom,description,'
                              'filepath,documenttype,date,est_publie',
                        'start': start,
                        'rows': rows,
                        'fq': 'date:[' + ANNEE + '-01-01T00:00:00Z TO ' + ANNEE + '-12-31T23:59:59Z]'
                    })

    lignes = []
    while len(result.docs) > 0:
        for doc_res in result.docs:
            parametrage = Parametrage.query.filter(Parametrage.siren == doc_res['siren']).first()
            COLL_NOM = parametrage.denomination
            DELIB_DATE = str(doc_res['date'][0].split("T", 1)[0])
            DELIB_ID = str(doc_res['documentidentifier'][0])
            DELIB_OBJET = str(doc_res['description'][0])
            COLL_SIRET = str(doc_res['siren'].zfill(9) + parametrage.nic)
            DELIB_MATIERE_CODE = str(doc_res['classification_code'])
            DELIB_MATIERE_NOM = str(doc_res['classification_nom'])

            BUDGET_ANNEE = ''
            BUDGET_NOM = ''
            PREF_ID = ''
            PREF_DATE = ''
            VOTE_EFFECTIF = ''
            VOTE_REEL = ''
            VOTE_POUR = ''
            VOTE_CONTRE = ''
            VOTE_ABSTENTION = ''
            if doc_res['est_publie'][0]:
                DELIB_URL = urllib.parse.quote(str(doc_res['filepath'][0]),safe="https://")
            else:
                DELIB_URL = ''

            line = '"' + COLL_NOM + '"' + ';' + '"' + COLL_SIRET + '"' + ';' + '"' + DELIB_ID + '"' + ';' + '"' + DELIB_DATE + '"' + ';' + '"' + DELIB_MATIERE_CODE + '"' + ';' \
                   + '"' + DELIB_MATIERE_NOM + '"' + ';' + '"' + DELIB_OBJET + '"' + ';' + '"' + BUDGET_ANNEE + '"' + ';' + '"' + BUDGET_NOM + '"' + ';' + '"' + PREF_ID + '"' + \
                   ';' + '"' + PREF_DATE + '"' + ';' + '"' + VOTE_EFFECTIF + '"' + ';' + '"' + VOTE_REEL + '"' + ';' + '"' + VOTE_POUR + '"' + ';' + '"' + VOTE_CONTRE + '"' + ';' \
                   + '"' + VOTE_ABSTENTION + '"' + ';' + '"' + DELIB_URL + '"' + '\n'
            lignes.append(line)
        start = start + rows
        result = \
            solr.search(q=query,
                        **{
                            'fl': 'siren,documentidentifier,classification_code,classification_nom,description,'
                                  'filepath,documenttype,date,est_publie',
                            'start': start,
                            'rows': rows,
                            'fq': 'date:[' + ANNEE + '-01-01T00:00:00Z TO ' + ANNEE + '-12-31T23:59:59Z]'
                        })

    # Ecriture du fichier scdl
    header = "COLL_NOM;COLL_SIRET;DELIB_ID;DELIB_DATE;DELIB_MATIERE_CODE;DELIB_MATIERE_NOM;DELIB_OBJET;BUDGET_ANNEE;BUDGET_NOM;PREF_ID;PREF_DATE;VOTE_EFFECTIF;VOTE_REEL;VOTE_POUR;VOTE_CONTRE;VOTE_ABSTENTION;DELIB_URL"
    f = open(csv_file_path, 'w')
    f.write(header + '\n')
    for ligne in lignes:
        try:
            f.write(ligne)
        except Exception:
            logging.exception("on ignore la ligne" + ligne)
    f.close()
    return filename

def api_url(path):
    API = current_app.config['API_DATAGOUV']
    return API + path


def publication_datagouv_scdl(annee, csv_file_path, type_acte):
    ANNEE = annee

    API_KEY = current_app.config['API_KEY_DATAGOUV']
    DATASET_BUDGET = current_app.config['DATASET_BUDGET_DATAGOUV']
    DATASET_DELIB = current_app.config['DATASET_DELIB_DATAGOUV']
    HEADERS = {
        'X-API-KEY': API_KEY,
    }

    # DELIBERATION
    if type_acte == '1':
        DATASET = DATASET_DELIB
    # BUDGET
    elif type_acte == '5':
        DATASET = DATASET_BUDGET

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
            # on update le fichier de la resource
            url = api_url('/datasets/{}/resources/{}/upload/'.format(DATASET, RESOURCE_UID))
            requests.post(url, files={
                'file': open(csv_file_path, 'rb'),
            }, headers=HEADERS)

        else:
            print('Creation de la resource annee ' + str(ANNEE))
            url = api_url('/datasets/{}/upload/'.format(DATASET))
            response = requests.post(url, files={
                'file': open(csv_file_path, 'rb'),
            }, headers=HEADERS)

            response = json.loads(response.text)
            RESOURCE_UID = response['id']

            # Mise à jour des métadonnées d’une ressource
            url = api_url('/datasets/{}/resources/{}/'.format(DATASET, RESOURCE_UID))
            if type_acte == '1':
                requests.put(url, json={
                    'format': 'xml',
                    'schema':
                        {'name': 'scdl/deliberations'}
                    ,
                }, headers=HEADERS)
            # BUDGET
            elif type_acte == '5':
                requests.put(url, json={
                    'format': 'xml',
                    'schema':
                        {'name': 'scdl/budget', 'version': '0.8.1'}
                    ,
                }, headers=HEADERS)

    return {'status': 'OK', 'message': 'publication scdl sur data.gouv', 'annee': str(ANNEE), 'type': str(type_acte)}
