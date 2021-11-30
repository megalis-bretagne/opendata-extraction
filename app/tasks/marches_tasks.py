import calendar
from xml.etree import ElementTree

from flask import current_app
from app.tasks.utils import *

from app import celeryapp
import json, requests
import time
from xml.dom import minidom
celery = celeryapp.celery


@celery.task(name='generation_marche')
def generation_marche():
    # generation annee
    t = time.localtime()
    ANNEE = time.strftime('%Y', t)
    return generation_and_publication_decp_pour_annee(ANNEE)

@celery.task(name='generation_marche_annee')
def generation_marche_annee(annee):
    return generation_and_publication_decp_pour_annee(annee)


@celery.task(name='generation_marche_histo')
def generation_marche_histo():
    annee_debut = 2014
    # generation annee
    t = time.localtime()
    annee_courante = int(time.strftime('%Y', t))
    annee_a_generer = annee_debut
    while annee_courante >= annee_a_generer:
        generation_and_publication_decp_pour_annee(str(annee_a_generer))
        annee_a_generer += 1
    print("END " + str(annee_a_generer))

def recuperer_decp(annee, siren):

    # generation annee
    ANNEE = annee
    url_jeton_sdm = current_app.config['URL_JETON_SDM']
    try:
        response = requests.get(url_jeton_sdm);
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
    except Exception as e:
        return "<?xml version=\"1.0\" encoding=\"UTF-8\"?><marches></marches>"

    return reponse_export_pivot


def generation_and_publication_decp_pour_annee(annee):
    clear_wordir()

    ANNEE = str(annee)
    url_jeton_sdm = current_app.config['URL_JETON_SDM']
    API_KEY = current_app.config['API_KEY_UDATA']
    DATASET = current_app.config['DATASET_MARCHE_UDATA']
    HEADERS = {
        'X-API-KEY': API_KEY,
    }

    try:
        response = requests.get(url_jeton_sdm);
        doc = minidom.parseString(response.text)
        jeton = doc.getElementsByTagName("ticket")[0].firstChild.data

        url_format_pivot = current_app.config['URL_API_DECP']

        # generation annee
        t = time.localtime()
        ANNEE_EN_COURS = time.strftime('%Y', t)
        MOIS_EN_COURS = time.strftime('%m', t)

        xml_data = None
        month=1
        while month <= 12:
            monthStr = "{:02d}".format(month)
            maxDay=calendar.monthrange(int(annee), month)[1]

            if int(annee) == int (ANNEE_EN_COURS):
                if (month > int(MOIS_EN_COURS)):
                    break

            reponse_export_pivot = requests.post(url_format_pivot, json={
                'token': jeton,
                'format': 'xml',
                'date_notif_min': '01-'+monthStr+'-' + str(ANNEE),
                'date_notif_max': str(maxDay)+'-'+monthStr+'-' + str(ANNEE)
            })

            data = ElementTree.fromstring(reponse_export_pivot.text)
            if xml_data is None:
                xml_data = data
            else:
                xml_data.extend(data)
            month=month+1

        # Ecriture du fichier dans dossier workdir
        f = open(get_or_create_workdir() + 'decp-' + str(ANNEE) + ' .xml', 'w',encoding='utf8')
        if xml_data is not None:
            xmlstr = ElementTree.tostring(xml_data, encoding='utf8', method='xml')
            f.write(xmlstr.decode("utf8"))
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

                # on supprime la resource
                url = api_url('/datasets/{}/resources/{}'.format(DATASET, RESOURCE_UID))
                response = requests.delete(url, headers=HEADERS);

                # ajout de la  nouvelle version du fichier
                url = api_url('/datasets/{}/upload/'.format(DATASET))
                response = requests.post(url, files={
                    'file': open(get_or_create_workdir() + 'decp-' + str(ANNEE) + ' .xml', 'rb'),
                }, headers=HEADERS)

                response = json.loads(response.text)
                RESOURCE_UID = response['id']

                # #Mise à jour des métadonnées d’une ressource
                url = api_url('/datasets/{}/resources/{}/'.format(DATASET, RESOURCE_UID))
                response = requests.put(url, json={
                    'format': 'xml',
                    'schema': {'name': '139bercy/format-commande-publique'}

                }, headers=HEADERS)

            else:
                print('Creation de la resource annee ' + str(ANNEE))

                # Mise à jour ressource
                url = api_url('/datasets/{}/upload/'.format(DATASET))
                response = requests.post(url, files={
                    'file': open(get_or_create_workdir() + 'decp-' + str(ANNEE) + ' .xml', 'rb'),
                }, headers=HEADERS)

                response = json.loads(response.text)
                RESOURCE_UID = response['id']

                # #Mise à jour des métadonnées d’une ressource
                url = api_url('/datasets/{}/resources/{}/'.format(DATASET, RESOURCE_UID))
                response = requests.put(url, json={
                    'format': 'xml',
                    'schema': {'name': '139bercy/format-commande-publique'}

                }, headers=HEADERS)

    except Exception as e:
        print("Erreur lors de la récupération du jeton SDM", e)

    return {'status': 'OK', 'message': 'publication decp sur data.gouv', 'annee': str(ANNEE)}

def api_url(path):
    API = current_app.config['API_UDATA']
    return API + path
