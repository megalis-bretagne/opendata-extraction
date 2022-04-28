import json
import logging
import os
import time
import urllib.parse

import requests
from flask import current_app

from app import celeryapp
from app.models.publication_model import Publication
from app.tasks import solr_connexion, clear_wordir, get_or_create_workdir

celery = celeryapp.celery


@celery.task(name='generation_and_publication_scdl')
def generation_and_publication_scdl(type, param_annee):
    t = time.localtime()
    annee = time.strftime('%Y', t)

    if param_annee is not None and len(param_annee) > 1 and 2014 <= int(param_annee) <= 2050:
        annee = param_annee

    if type == '1':
        filename = generation_deliberation("*", annee, 'opendata_active')
        publication_datagouv_scdl(annee, get_or_create_workdir() + filename, type)
    elif type == '5':
        filename = generation_budget("*", annee, 'opendata_active')
        publication_datagouv_scdl(annee, get_or_create_workdir() + filename, type)

    return {'status': 'OK', 'message': 'generation et publication scdl', 'annee': str(annee), 'type': str(type)}


def generation_budget(siren, annee, flag_active=None):
    clear_wordir()
    ANNEE = str(annee)
    SIREN = str(siren)

    TYPE = '5'
    # connexion solr
    solr = solr_connexion()

    start = 0
    rows = 100

    # construction de la requete solr
    query = 'typology: 99_BU AND est_publie: True AND documenttype:' + str(TYPE) + ' AND date_budget:' + str(ANNEE)
    if str(siren) == '*':
        filename = 'BUDGET-' + ANNEE + '.csv'
    else:
        filename = 'BUDGET-' + SIREN + '-' + ANNEE + '.csv'
        query = query + ' AND siren:' + str(siren)

    if flag_active is not None:
        query = query + ' AND ' + flag_active + ': True '

    # generation de l'url du fichier scdl
    csv_file_path = get_or_create_workdir() + filename

    # On recherche dans apache solr les documents pour un SIREN et un TYPE (deliberation, budget ...) et on fitre sur l'année passée en parametre ANNEE
    result = \
        solr.search(q=query,
                    **{
                        'fl': 'entity,nic,siren,documentidentifier,classification_code,classification_nom,description,'
                              'filepath,documenttype,date,est_publie,date_budget,publication_id',
                        'start': start,
                        'rows': rows
                    })
    # Ecriture du fichier scdl
    header = "BGT_NATDEC,BGT_ANNEE,BGT_SIRET,BGT_NOM,BGT_CONTNAT,BGT_CONTNAT_LABEL,BGT_NATURE,BGT_NATURE_LABEL,BGT_FONCTION,BGT_FONCTION_LABEL,BGT_OPERATION,BGT_SECTION,BGT_OPBUDG,BGT_CODRD,BGT_MTREAL,BGT_MTBUDGPREC,BGT_MTRARPREC,BGT_MTPROPNOUV,BGT_MTPREV,BGT_CREDOUV,BGT_MTRAR3112,BGT_ARTSPE"
    f = open(csv_file_path, 'w')
    f.write(header + '\n')
    f.close()

    while len(result.docs) > 0:
        # pour tous les fichiers budget qu'on retrouve dans la bdd
        for doc_res in result.docs:
            url = str(doc_res['filepath'][0])
            try:
                # on récupère la publication à publier en BDD
                publication = Publication.query.filter(Publication.id == doc_res['publication_id']).one()
                for acte in publication.actes:
                    totem2_csv_and_concat_scdl(acte.path, csv_file_path)
            except Exception:
                print("fichier ignore :" + url)
                logging.exception("exeption dans totem2csvAndConcatscdl")
        start = start + rows
        result = \
            solr.search(
                q=query,
                **{
                    'fl': 'entity,nic,siren,documentidentifier,classification_code,classification_nom,description,'
                          'filepath,documenttype,date,est_publie,date_budget,publication_id',
                    'start': start,
                    'rows': rows
                })
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
    rows = 100

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
                        'fl': 'entity,nic,siren,documentidentifier,classification_code,classification_nom,description,'
                              'filepath,documenttype,date,est_publie',
                        'start': start,
                        'rows': rows,
                        'fq': 'date:[' + ANNEE + '-01-01T00:00:00Z TO ' + ANNEE + '-12-31T23:59:59Z]'
                    })

    lignes = []
    while len(result.docs) > 0:
        for doc_res in result.docs:

            COLL_NOM = str(doc_res['entity'][0])
            DELIB_DATE = str(doc_res['date'][0].split("T", 1)[0])
            DELIB_ID = str(doc_res['documentidentifier'][0])
            DELIB_OBJET = str(doc_res['description'][0])
            COLL_SIRET = str(doc_res['siren'].zfill(9)) + str(doc_res['nic'].zfill(5))
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
                            'fl': 'entity,nic,siren,documentidentifier,classification_code,classification_nom,description,'
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


def totem2_csv_and_concat_scdl(totemfile, csv_budget_scdl):
    # on appelle de code récupéré ici
    # https://gitlab.com/datafin/totem.git

    if os.path.exists("/tmp/totem.xml"):
        os.remove("/tmp/totem.xml")
    if os.path.exists("/tmp/totem.csv"):
        os.remove("/tmp/totem.csv")

    bash_command = "shared/totem/totem2csv/totem2csv.sh %s %s" % (totemfile, "output_prefix")
    import subprocess
    logging.info("bash_command: %s", bash_command)
    process = subprocess.Popen(["bash", "-c", bash_command], stdout=subprocess.PIPE)
    output, error = process.communicate()
    logging.info(output)
    if error is not None:
        raise error

    try:
        logging.info("concaténation du totem csv dans scdl %s", csv_budget_scdl)
        scdl_budget = open(csv_budget_scdl, 'a')
        with open('/tmp/totem.csv') as infile:
            for line in infile:
                scdl_budget.write(line)
        scdl_budget.close()
    except Exception as e:
        logging.exception("Error occured while concat scdl budget")
        raise e

    return 0


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
