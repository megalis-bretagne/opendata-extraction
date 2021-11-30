import tempfile
from app import celeryapp
import json, requests

from app.models.publication_model import Publication
from app.tasks.utils import *
import time
import urllib
from flask import current_app

celery = celeryapp.celery


@celery.task(name='generation_and_publication_SCDL')
def generation_and_publication_SCDL(type, param_annee):
    # on clear le workdir
    clear_wordir()

    # generation annee
    t = time.localtime()
    ANNEE = time.strftime('%Y', t)

    if param_annee is not None and len(param_annee) > 1:
        if 2014 <= int(param_annee) <= 2050:
            ANNEE = param_annee

    TYPE = type
    # connexion solr
    solr = solr_connexion()

    start = 0
    rows = 100

    # CAS DELIBERATION
    if TYPE == '1':

        # creation du nom du fichier SCDL
        # filename = 'DELIB-' + ANNEE +'.csv'
        filename = 'DELIBERATION-' + ANNEE + '.csv'
        # generation de l'url du fichier SCDL
        csvFilePath = get_or_create_workdir() + filename

        # On recherche dans apache solr les documents pour un SIREN et un TYPE (deliberation, budget ...) et on fitre sur l'année passée en parametre ANNEE
        result = \
            solr.search(q='opendata_active: True AND typology: 99_DE AND documenttype:' + str(TYPE) + ' ',
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
                COLL_SIRET = str(doc_res['siren'][0]) + str(doc_res['nic'][0])
                DELIB_ID = str(doc_res['documentidentifier'][0])
                dateActe = doc_res['date'][0].split("T", 1)
                DELIB_DATE = str(dateActe[0])
                DELIB_MATIERE_CODE = str(doc_res['classification_code'][0])
                DELIB_MATIERE_NOM = str(doc_res['classification_nom'][0])
                DELIB_OBJET = str(doc_res['description'][0])
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
                    DELIB_URL = str(doc_res['filepath'][0])
                else:
                    DELIB_URL = ''

                line = '"' + COLL_NOM + '"' + ';' + '"' + COLL_SIRET + '"' + ';' + '"' + DELIB_ID + '"' + ';' + '"' + DELIB_DATE + '"' + ';' + '"' + DELIB_MATIERE_CODE + '"' + ';' \
                       + '"' + DELIB_MATIERE_NOM + '"' + ';' + '"' + DELIB_OBJET + '"' + ';' + '"' + BUDGET_ANNEE + '"' + ';' + '"' + BUDGET_NOM + '"' + ';' + '"' + PREF_ID + '"' + \
                       ';' + '"' + PREF_DATE + '"' + ';' + '"' + VOTE_EFFECTIF + '"' + ';' + '"' + VOTE_REEL + '"' + ';' + '"' + VOTE_POUR + '"' + ';' + '"' + VOTE_CONTRE + '"' + ';' \
                       + '"' + VOTE_ABSTENTION + '"' + ';' + '"' + DELIB_URL + '"' + '\n'
                lignes.append(line)

            start = start + rows
            # On recherche dans apache solr les documents pour un SIREN et un TYPE (deliberation, budget ...) et on fitre sur l'année passée en parametre ANNEE
            result = \
                solr.search(q='opendata_active: True AND typology: 99_DE AND documenttype:' + str(TYPE) + ' ',
                            **{
                                'fl': 'entity,nic,siren,documentidentifier,classification_code,classification_nom,description,'
                                      'filepath,documenttype,date,est_publie',
                                'start': start,
                                'rows': rows,
                                'fq': 'date:[' + ANNEE + '-01-01T00:00:00Z TO ' + ANNEE + '-12-31T23:59:59Z]'
                            })

        # Ecriture du fichier SCDL
        header = "COLL_NOM;COLL_SIRET;DELIB_ID;DELIB_DATE;DELIB_MATIERE_CODE;DELIB_MATIERE_NOM;DELIB_OBJET;BUDGET_ANNEE;BUDGET_NOM;PREF_ID;PREF_DATE;VOTE_EFFECTIF;VOTE_REEL;VOTE_POUR;VOTE_CONTRE;VOTE_ABSTENTION;DELIB_URL"
        f = open(csvFilePath, 'w')
        f.write(header + '\n')
        for ligne in lignes:
            try:
                f.write(ligne)
            except Exception as e:
                logging.exception("on ignore la ligne" + ligne)
        f.close()
        if len(lignes) > 0:
            publication_udata_scdl(ANNEE, csvFilePath, TYPE)


    # CAS BUDGET
    elif TYPE == '5':

        filename = 'BUDGET-' + ANNEE + '.csv'
        # generation de l'url du fichier SCDL
        csvFilePath = get_or_create_workdir() + filename

        # On recherche dans apache solr les documents pour un SIREN et un TYPE (deliberation, budget ...) et on fitre sur l'année passée en parametre ANNEE
        result = \
            solr.search(q='opendata_active: True AND typology: 99_BU AND est_publie: True AND documenttype:' + str(
                TYPE) + ' AND date_budget:' + str(ANNEE) + ' ',
                        **{
                            'fl': 'entity,nic,siren,documentidentifier,classification_code,classification_nom,description,'
                                  'filepath,documenttype,date,est_publie,date_budget,publication_id',
                            'start': start,
                            'rows': rows
                        })

        # Ecriture du fichier SCDL
        header = "BGT_NATDEC,BGT_ANNEE,BGT_SIRET,BGT_NOM,BGT_CONTNAT,BGT_CONTNAT_LABEL,BGT_NATURE,BGT_NATURE_LABEL,BGT_FONCTION,BGT_FONCTION_LABEL,BGT_OPERATION,BGT_SECTION,BGT_OPBUDG,BGT_CODRD,BGT_MTREAL,BGT_MTBUDGPREC,BGT_MTRARPREC,BGT_MTPROPNOUV,BGT_MTPREV,BGT_CREDOUV,BGT_MTRAR3112,BGT_ARTSPE"
        f = open(csvFilePath, 'w')
        f.write(header + '\n')
        f.close()

        while len(result.docs) > 0:
            # pour tous les fichiers budget qu'on retrouve dans la bdd
            for doc_res in result.docs:
                url = str(doc_res['filepath'][0])
                try:
                    # on récupère la publication à publier en BDD
                    publication = Publication.query.filter(Publication.id == doc_res['publication_id'][0]).one()
                    for acte in publication.actes:
                        totem2csvAndConcatSCDL(acte.path, csvFilePath)
                except Exception as e:
                    print("fichier ignore :" + url)
                    logging.exception("exeption dans totem2csvAndConcatSCDL")
            start = start + rows
            result = \
                solr.search(q='opendata_active: True AND typology: 99_BU AND est_publie: True AND documenttype:' + str(
                    TYPE) + ' AND date_budget:' + str(ANNEE) + ' ',
                            **{
                                'fl': 'entity,nic,siren,documentidentifier,classification_code,classification_nom,description,'
                                      'filepath,documenttype,date,est_publie,date_budget,publication_id',
                                'start': start,
                                'rows': rows
                            })
        # On envoie le fichier SCDL dans le dossier
        publication_udata_scdl(ANNEE, csvFilePath, TYPE)

    return {'status': 'OK', 'message': 'generation et publication SCDL', 'annee': str(ANNEE),
            'type': str(type)}


def generation_SCDL(type, siren, annee):
    # on clear le workdir
    clear_wordir()
    ANNEE = str(annee)
    SIREN = str(siren)

    TYPE = type
    # connexion solr
    solr = solr_connexion()

    start = 0
    rows = 100

    # CAS DELIBERATION
    if TYPE == '1':
        # creation du nom du fichier SCDL
        # filename = 'DELIBERATION-' + ANNEE +'.csv'
        if str(siren) == '*':
            filename = 'DELIBERATION-' + ANNEE + '.csv'
            query = 'opendata_active: True AND typology: 99_DE AND documenttype:' + str(TYPE) + ' '
        else:
            filename = 'DELIBERATION-' + SIREN + '-' + ANNEE + '.csv'
            query = 'siren:' + SIREN + ' AND typology: 99_DE AND documenttype:' + str(TYPE) + ' '
        # generation de l'url du fichier SCDL
        csvFilePath = get_or_create_workdir() + filename

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
                COLL_SIRET = str(doc_res['siren'][0]) + str(doc_res['nic'][0])
                DELIB_ID = str(doc_res['documentidentifier'][0])
                dateActe = doc_res['date'][0].split("T", 1)
                DELIB_DATE = str(dateActe[0])
                DELIB_MATIERE_CODE = str(doc_res['classification_code'][0])
                DELIB_MATIERE_NOM = str(doc_res['classification_nom'][0])
                DELIB_OBJET = str(doc_res['description'][0])
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
                    DELIB_URL = str(doc_res['filepath'][0])
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

        # Ecriture du fichier SCDL
        header = "COLL_NOM;COLL_SIRET;DELIB_ID;DELIB_DATE;DELIB_MATIERE_CODE;DELIB_MATIERE_NOM;DELIB_OBJET;BUDGET_ANNEE;BUDGET_NOM;PREF_ID;PREF_DATE;VOTE_EFFECTIF;VOTE_REEL;VOTE_POUR;VOTE_CONTRE;VOTE_ABSTENTION;DELIB_URL"
        f = open(csvFilePath, 'w')
        f.write(header + '\n')
        for ligne in lignes:
            f.write(ligne)
        f.close()

    # CAS BUDGET
    elif TYPE == '5':
        if str(siren) == '*':
            filename = 'BUDGET-' + ANNEE + '.csv'
            query = 'opendata_active: True AND typology: 99_BU AND est_publie: True AND documenttype:' + str(
                TYPE) + ' AND date_budget:' + str(ANNEE) + ' '
        else:
            filename = 'BUDGET-' + SIREN + '-' + ANNEE + '.csv'
            query = 'est_publie: True AND typology: 99_BU AND siren:' + str(siren) + ' AND documenttype:' + str(
                TYPE) + ' AND date_budget:' + str(ANNEE) + ' '
        # generation de l'url du fichier SCDL
        csvFilePath = get_or_create_workdir() + filename

        # On recherche dans apache solr les documents pour un SIREN et un TYPE (deliberation, budget ...) et on fitre sur l'année passée en parametre ANNEE
        result = \
            solr.search(q=query,
                        **{
                            'fl': 'entity,nic,siren,documentidentifier,classification_code,classification_nom,description,'
                                  'filepath,documenttype,date,est_publie,date_budget,publication_id',
                            'start': start,
                            'rows': rows
                        })
        # Ecriture du fichier SCDL
        header = "BGT_NATDEC,BGT_ANNEE,BGT_SIRET,BGT_NOM,BGT_CONTNAT,BGT_CONTNAT_LABEL,BGT_NATURE,BGT_NATURE_LABEL,BGT_FONCTION,BGT_FONCTION_LABEL,BGT_OPERATION,BGT_SECTION,BGT_OPBUDG,BGT_CODRD,BGT_MTREAL,BGT_MTBUDGPREC,BGT_MTRARPREC,BGT_MTPROPNOUV,BGT_MTPREV,BGT_CREDOUV,BGT_MTRAR3112,BGT_ARTSPE"
        f = open(csvFilePath, 'w')
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
                        totem2csvAndConcatSCDL(acte.path, csvFilePath)
                except Exception as e:
                    print("fichier ignore :" + url)
                    logging.exception("exeption dans totem2csvAndConcatSCDL")
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


def totem2csvAndConcatSCDL(totemfile, csvBudgetSCDL):
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
        logging.info("concaténation du totem csv dans SCDL %s", csvBudgetSCDL)
        scdlBudget = open(csvBudgetSCDL, 'a')
        with open('/tmp/totem.csv') as infile:
            for line in infile:
                scdlBudget.write(line)
        scdlBudget.close()
    except Exception as e:
        logging.exception("Error occured while concat SCDL budget")
        raise e

    return 0


def api_url(path):
    API = current_app.config['API_UDATA']
    return API + path


def publication_udata_scdl(annee, csvFilePath, type_acte):
    ANNEE = annee

    API_KEY = current_app.config['API_KEY_UDATA']
    DATASET_BUDGET = current_app.config['DATASET_BUDGET_UDATA']
    DATASET_DELIB = current_app.config['DATASET_DELIB_UDATA']
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
            response = requests.post(url, files={
                'file': open(csvFilePath, 'rb'),
            }, headers=HEADERS)

        else:
            print('Creation de la resource annee ' + str(ANNEE))
            url = api_url('/datasets/{}/upload/'.format(DATASET))
            response = requests.post(url, files={
                'file': open(csvFilePath, 'rb'),
            }, headers=HEADERS)

            response = json.loads(response.text)
            RESOURCE_UID = response['id']

            # Mise à jour des métadonnées d’une ressource
            url = api_url('/datasets/{}/resources/{}/'.format(DATASET, RESOURCE_UID))
            if type_acte == '1':
                response = requests.put(url, json={
                    'format': 'xml',
                    'schema':
                        {'name': 'scdl/deliberations'}
                    ,
                }, headers=HEADERS)
            # BUDGET
            elif type_acte == '5':
                response = requests.put(url, json={
                    'format': 'xml',
                    'schema':
                        {'name': 'scdl/budget', 'version': '0.8.1'}
                    ,
                }, headers=HEADERS)

    return {'status': 'OK', 'message': 'publication SCDL sur data.gouv', 'annee': str(ANNEE)}
