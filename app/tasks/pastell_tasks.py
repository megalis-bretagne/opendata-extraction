import json
import logging
import requests
from flask import current_app
from requests.auth import HTTPBasicAuth
from app import celeryapp
from app.tasks.utils import PastellApiException

celery = celeryapp.celery


@celery.task(name='creation_et_association_all_task')
def creation_et_association_all():
    URL_API_PASTELL = current_app.config['API_PASTELL_URL']
    API_PASTELL_VERSION = current_app.config['API_PASTELL_VERSION']

    auth_pastell = HTTPBasicAuth(current_app.config['API_PASTELL_USER'], current_app.config['API_PASTELL_PASSWORD'])
    liste_entite_reponse = requests.get(
        URL_API_PASTELL + API_PASTELL_VERSION + "/entite", auth=auth_pastell)
    if liste_entite_reponse.status_code == 200:
        liste_entite = json.loads(liste_entite_reponse.text)

        for entite in liste_entite:
            creation_et_association_connecteur_transformateur_task.delay(entite['id_e'])
            creation_et_association_connecteur_ged_sftp_task.delay(entite['id_e'])
            creation_et_association_connecteur_ged_megalis_opendata_task.delay(entite['id_e'])
            creation_et_association_connecteur_ged_pastell_AG_task.delay(entite['id_e'])

        nb_entite = len(liste_entite)
        return {'status': 'OK', 'message': 'creation_et_association_all_task', 'nb_id_e': str(nb_entite)}

    else:
        return {'status': 'KO', 'message': 'creation_et_association_all_task'}


@celery.task(name='mise_en_place_config_pastell_task')
def mise_en_place_config_pastell(id_e):
    creation_et_association_connecteur_transformateur_task.delay(id_e)
    creation_et_association_connecteur_ged_sftp_task.delay(id_e)
    creation_et_association_connecteur_ged_megalis_opendata_task.delay(id_e)
    creation_et_association_connecteur_ged_pastell_AG_task.delay(id_e)
    return {'status': 'OK', 'message': 'mise_en_place_config_pastell', 'id_e': str(id_e)}


@celery.task(name='routine_parametrage_pastell_task')
def routine_parametrage_pastell():
    """Tâche qui recherche les entites qui ont des documents open data pastell dans un état incorrect
        preparation-send-ged_1 ou preparation-transformation
    , cela signifie qu'il faut mettre en place le paramétrage pastell pour l'entité
    On log si autre état trouvé

    """
    URL_API_PASTELL = current_app.config['API_PASTELL_URL']
    API_PASTELL_VERSION = current_app.config['API_PASTELL_VERSION']
    auth_pastell = HTTPBasicAuth(current_app.config['API_PASTELL_USER'], current_app.config['API_PASTELL_PASSWORD'])

    response = requests.get(URL_API_PASTELL + API_PASTELL_VERSION + "/document/count?type=ged-megalis-opendata",
                            auth=auth_pastell)

    if response.ok:
        res = json.loads(response.text)
        liste_entite_preparation_send = []
        liste_entite_transformation = []

        for entite in res:
            etat_innattendu_trouve = False

            if len(res[str(entite)]['flux']['ged-megalis-opendata']) > 0:

                for etat in res[str(entite)]['flux']['ged-megalis-opendata']:

                    # on ignore les docs à l'état terminé
                    if (etat != 'termine'):
                        if etat == 'preparation-send-ged_1':
                            liste_entite_preparation_send.append(entite)
                            break;
                        elif etat == 'preparation-transformation':
                            liste_entite_transformation.append(entite)
                            break;
                        # pour tous les autres état on log
                        else:
                            etat_innattendu_trouve = True
                            result = "id_e:" + str(entite) + " => "
                            result += str(etat) + " "

                if etat_innattendu_trouve:
                    logging.info(result)

        for id_e in liste_entite_preparation_send:
            mise_en_place_config_pastell.delay(id_e)
            deblocage_ged_pastell.delay(id_e, "preparation-send-ged_1")

        for id_e in liste_entite_transformation:
            mise_en_place_config_pastell.delay(id_e)
            deblocage_ged_pastell.delay(id_e, "preparation-transformation")

        return {'status': 'OK', 'nombre': str(len(liste_entite_preparation_send) + len(liste_entite_transformation)),
                'message': 'routine de mise en place du paramétrage pastell effectue'}
    else:
        raise PastellApiException("Problème lors de l'appel à l'api /document/count de pastell")


@celery.task(name='deblocage_ged_pastell_task')
def deblocage_ged_pastell(id_e, last_etat):
    if last_etat == 'preparation-send-ged_1':
        ACTION = 'send-ged_1'
    elif last_etat == 'preparation-transformation':
        ACTION = 'transformation'
    else:
        return {'status': 'OK', 'message': 'action non gere', 'action': str(last_etat)}

    URL_API_PASTELL = current_app.config['API_PASTELL_URL']
    API_PASTELL_VERSION = current_app.config['API_PASTELL_VERSION']
    auth_pastell = HTTPBasicAuth(current_app.config['API_PASTELL_USER'], current_app.config['API_PASTELL_PASSWORD'])
    ID_E_PASTELL = id_e

    response = requests.get(
        URL_API_PASTELL + API_PASTELL_VERSION + "/entite/" + ID_E_PASTELL + "/document?&type=ged-megalis-opendata&lastetat=" + last_etat,
        auth=auth_pastell)

    if response.ok:
        res = json.loads(response.text)
        for doc in res:
            requests.post(URL_API_PASTELL + API_PASTELL_VERSION + "/entite/" + id_e + "/document/" + doc['id_d'] +
                          '/action/' + ACTION, auth=auth_pastell)
    else:
        raise PastellApiException("Problème lors de l'appel à l'api /document/count de pastell")

    return {'status': 'OK', 'id_e': str(id_e), 'message': 'deblocage pastell effectue'}


@celery.task(name='creation_et_association_connecteur_ged_pastell_AG_task')
def creation_et_association_connecteur_ged_pastell_AG_task(id_e):
    URL_API_PASTELL = current_app.config['API_PASTELL_URL']
    API_PASTELL_VERSION = current_app.config['API_PASTELL_VERSION']

    ID_E_PASTELL = id_e

    # ETAPE 1: Creation du connecteur sans sa configuration
    auth_pastell = HTTPBasicAuth(current_app.config['API_PASTELL_USER'], current_app.config['API_PASTELL_PASSWORD'])

    data = {
        "id_e": ID_E_PASTELL,
        "libelle": 'ged-megalis-opendata-auto-AG',
        "id_connecteur": 'depot-pastell',
        "type": 'GED',
        "id_verrou": ""
    }
    response = requests.post(URL_API_PASTELL + API_PASTELL_VERSION + "/entite/" + ID_E_PASTELL + "/connecteur/", data,
                             auth=auth_pastell)
    if response.ok:
        # ETAPE 2: configuration du connecteur précédemment créé
        res = json.loads(response.text)
        data_detail = {
            "pastell_url": URL_API_PASTELL,
            "pastell_login": current_app.config['API_PASTELL_USER'],
            "pastell_password": current_app.config['API_PASTELL_PASSWORD'],
            "pastell_id_e": ID_E_PASTELL,
            "pastell_type_dossier": "ged-megalis-opendata",
            "pastell_metadata": "publication_open_data:2\nacte_nature:%acte_nature%\nnumero_de_lacte:%numero_de_lacte%\nobjet:%objet%\narrete:%arrete%\nacte_tamponne:%acte_tamponne%\nautre_document_attache:%autre_document_attache%\nclassification:%classification%\ntype_piece:%type_piece%\ndate_de_lacte:%date_de_lacte%",
            "pastell_action": 'orientation'
        }
        responseConnecteur = requests.patch(
            URL_API_PASTELL + API_PASTELL_VERSION + "/entite/" + ID_E_PASTELL + "/connecteur/" + res[
                'id_ce'] + '/content/', data=data_detail,
            auth=auth_pastell)

        if responseConnecteur.ok:
            # ETAPE 3: Association du nouveau connecteur avec l'entite pastell pour un type de flux
            resquest = {
                'type': 'GED'
            }
            # Association actes-generique
            ID_FLUX = "actes-generique"
            responseAssociation = requests.post(
                URL_API_PASTELL + API_PASTELL_VERSION + "/entite/" + ID_E_PASTELL + "/flux/" + ID_FLUX + '/connecteur/' +
                res[
                    'id_ce'] + '/',
                data=resquest, auth=auth_pastell)
            if responseAssociation.ok:
                logging.info('Association connecteur ged_pastell ok type_flux:%s, id_e:%s', ID_FLUX, ID_E_PASTELL)
                return {'status': 'OK', 'message': 'Association connecteur ged_pastell ok', 'id_e': str(id_e),
                        'ID_FLUX': str(ID_FLUX)}
            else:
                logging.error('Association connecteur ged_pastell KO erreur:%s', responseAssociation.text)

        else:
            logging.error('Creation config connecteur ged_pastell KO erreur:%s', responseConnecteur.text)
    else:
        logging.error('Creation connecteur ged_pastell KO erreur:%s', response.text)

    return {'status': 'KO', 'message': 'Association connecteur ged_pastell KO', 'id_e': str(id_e),
            'ID_FLUX': str(ID_FLUX)}


@celery.task(name='creation_et_association_connecteur_ged_sftp_task')
def creation_et_association_connecteur_ged_sftp_task(id_e):
    URL_API_PASTELL = current_app.config['API_PASTELL_URL']
    API_PASTELL_VERSION = current_app.config['API_PASTELL_VERSION']

    ID_E_PASTELL = id_e

    # ETAPE 1: Creation du connecteur sans sa configuration
    auth_pastell = HTTPBasicAuth(current_app.config['API_PASTELL_USER'], current_app.config['API_PASTELL_PASSWORD'])

    data = {
        "id_e": ID_E_PASTELL,
        "libelle": 'ged-sftp-opendata-auto',
        "id_connecteur": 'depot-sftp',
        "type": 'GED',
        "id_verrou": ""
    }
    response = requests.post(URL_API_PASTELL + API_PASTELL_VERSION + "/entite/" + ID_E_PASTELL + "/connecteur/", data,
                             auth=auth_pastell)
    if response.ok:

        # ETAPE 2: configuration du connecteur précédemment créé
        res = json.loads(response.text)

        data_detail = {
            "depot_type_depot": '2',
            "depot_titre_repertoire": '3',
            "depot_titre_expression": '',
            "depot_metadonnees": '3',
            "depot_metadonnes_filename": '',
            "depot_metadonnees_restriction": '',
            "depot_pastell_file_filename": '1',
            "depot_file_restriction": '',
            "depot_filename_replacement_regexp": '',
            "depot_filename_preg_match": '',
            "depot_creation_fichier_termine": '',
            "depot_nom_fichier_termine": '',
            "depot_existe_deja": '2',
            "depot_sftp_host": current_app.config['DEPOT_HOSTNAME'],
            "depot_sftp_port": '22',
            "depot_sftp_login": current_app.config['DEPOT_USERNAME'],
            "depot_sftp_password": current_app.config['DEPOT_PASSWORD'],
            "depot_sftp_fingerprint": current_app.config['DEPOT_FINGERPRINT'],
            "depot_sftp_directory": '/data/partage/opendata' + current_app.config['DIRECTORY_TO_WATCH'],
            "depot_sftp_rename_suffix": ''
        }
        responseConnecteur = requests.patch(
            URL_API_PASTELL + API_PASTELL_VERSION + "/entite/" + ID_E_PASTELL + "/connecteur/" + res[
                'id_ce'] + '/content/', data=data_detail,
            auth=auth_pastell)

        if responseConnecteur.ok:
            # ETAPE 3: Association du nouveau connecteur avec l'entite pastell pour un type de flux
            resquest = {
                'type': 'GED'
            }
            ID_FLUX = 'ged-megalis-opendata'
            responseAssociation = requests.post(
                URL_API_PASTELL + API_PASTELL_VERSION + "/entite/" + ID_E_PASTELL + "/flux/" + ID_FLUX + '/connecteur/' +
                res[
                    'id_ce'] + '/',
                data=resquest, auth=auth_pastell)
            if responseAssociation.ok:
                logging.info('Association connecteur ged_sftp ok type_flux:%s, id_e:%s', ID_FLUX, ID_E_PASTELL)

                return {'status': 'OK', 'message': 'Association connecteur ged_sftp ok', 'id_e': str(id_e),
                        'ID_FLUX': str(ID_FLUX)}
            else:
                logging.error('Association connecteur ged_sftp KO type_flux:%s, id_e:%s', ID_FLUX, ID_E_PASTELL)
                logging.error('Association connecteur ged_sftp KO erreur:%s', responseAssociation.text)
        else:
            logging.error('Creation config connecteur ged_sftp KO erreur:%s', responseConnecteur.text)
    else:
        logging.error('Creation connecteur ged_sftp KO erreur:%s', response.text)

    return {'status': 'KO', 'message': 'Association connecteur ged_sftp KO', 'id_e': str(id_e),
            'ID_FLUX': str(ID_FLUX)}


@celery.task(name='creation_et_association_connecteur_transformateur_task')
def creation_et_association_connecteur_transformateur_task(id_e):
    URL_API_PASTELL = current_app.config['API_PASTELL_URL']
    API_PASTELL_VERSION = current_app.config['API_PASTELL_VERSION']

    ID_E_PASTELL = id_e

    # ETAPE 1: Creation du connecteur sans sa configuration
    auth_pastell = HTTPBasicAuth(current_app.config['API_PASTELL_USER'], current_app.config['API_PASTELL_PASSWORD'])

    data = {
        "id_e": ID_E_PASTELL,
        "libelle": 'transfo-ajout-siren-auto',
        "id_connecteur": 'transformation-generique',
        "type": 'transformation',
        "id_verrou": ""
    }
    response = requests.post(URL_API_PASTELL + API_PASTELL_VERSION + "/entite/" + ID_E_PASTELL + "/connecteur/", data,
                             auth=auth_pastell)
    if response.ok:

        # ETAPE 2: configuration du connecteur précédemment créé
        res = json.loads(response.text)

        data_detail = {'file_name': 'definition.json'}
        file = {
            'file_content': open("app/definition.json", "rb")}
        responseConnecteur = requests.post(URL_API_PASTELL + API_PASTELL_VERSION + "/entite/" + ID_E_PASTELL +
                                           "/connecteur/" + res['id_ce'] + '/file/definition', data=data_detail,
                                           auth=auth_pastell,
                                           files=file)
        if responseConnecteur.ok:
            # ETAPE 3: Association du nouveau connecteur avec l'entite pastell pour un type de flux
            resquest = {
                'type': 'transformation'
            }
            ID_FLUX = 'ged-megalis-opendata'
            responseAssociation = requests.post(
                URL_API_PASTELL + API_PASTELL_VERSION + "/entite/" + ID_E_PASTELL + "/flux/" + ID_FLUX + '/connecteur/' +
                res[
                    'id_ce'] + '/',
                data=resquest, auth=auth_pastell)
            if responseAssociation.ok:
                logging.info('Association connecteur transformation ok type_flux:%s, id_e:%s', ID_FLUX, ID_E_PASTELL)
                return {'status': 'OK', 'message': 'Association connecteur transformation ok', 'id_e': str(id_e),
                        'ID_FLUX': str(ID_FLUX)}
            else:
                logging.error('Association connecteur transformation KO erreur:%s', responseAssociation.text)
        else:
            logging.error('Creation config connecteur transformation KO erreur:%s', responseConnecteur.text)
    else:
        logging.error('Creation connecteur transformation KO erreur:%s', response.text)

    return {'status': 'KO', 'message': 'Association connecteur transformation KO', 'id_e': str(id_e),
            'ID_FLUX': str(ID_FLUX)}


@celery.task(name='creation_et_association_connecteur_ged_megalis_opendata_task')
def creation_et_association_connecteur_ged_megalis_opendata_task(id_e):
    URL_API_PASTELL = current_app.config['API_PASTELL_URL']
    API_PASTELL_VERSION = current_app.config['API_PASTELL_VERSION']

    ID_E_PASTELL = id_e

    # ETAPE 1: Creation du connecteur sans sa configuration
    auth_pastell = HTTPBasicAuth(current_app.config['API_PASTELL_USER'], current_app.config['API_PASTELL_PASSWORD'])

    data = {
        "id_e": ID_E_PASTELL,
        "libelle": 'ged-megalis-opendata-auto',
        "id_connecteur": 'depot-pastell',
        "type": 'GED',
        "id_verrou": ""
    }

    response = requests.post(URL_API_PASTELL + API_PASTELL_VERSION + "/entite/" + ID_E_PASTELL + "/connecteur/", data,
                             auth=auth_pastell)
    if response.ok:
        # ETAPE 2: configuration du connecteur précédemment créé
        res = json.loads(response.text)
        data_detail = {
            "pastell_url": URL_API_PASTELL,
            "pastell_login": 'admin',
            "pastell_password": 'MegalisSibAdmin',
            "pastell_id_e": ID_E_PASTELL,
            "pastell_type_dossier": "ged-megalis-opendata",
            "pastell_metadata": "publication_open_data:%publication_open_data%\nacte_nature:%acte_nature%\nnumero_de_lacte:%numero_de_lacte%\nobjet:%objet%\narrete:%arrete%\nacte_tamponne:%acte_tamponne%\nautre_document_attache:%autre_document_attache%\nclassification:%classification%\ntype_piece:%type_piece%\ndate_de_lacte:%date_de_lacte%",
            "pastell_action": 'orientation'
        }
        responseConnecteur = requests.patch(
            URL_API_PASTELL + API_PASTELL_VERSION + "/entite/" + ID_E_PASTELL + "/connecteur/" + res[
                'id_ce'] + '/content/', data=data_detail,
            auth=auth_pastell)

        if responseConnecteur.ok:
            # ETAPE 3: Association du nouveau connecteur avec l'entite pastell pour un type de flux
            resquest = {
                'type': 'GED'
            }
            # Association deliberations-studio
            ID_FLUX = "deliberations-studio"
            responseAssociationDelib = requests.post(
                URL_API_PASTELL + API_PASTELL_VERSION + "/entite/" + ID_E_PASTELL + "/flux/" + ID_FLUX + '/connecteur/' +
                res[
                    'id_ce'] + '/',
                data=resquest, auth=auth_pastell)

            ID_FLUX = "autres-studio"
            responseAssociationAutres = requests.post(
                URL_API_PASTELL + API_PASTELL_VERSION + "/entite/" + ID_E_PASTELL + "/flux/" + ID_FLUX + '/connecteur/' +
                res[
                    'id_ce'] + '/',
                data=resquest, auth=auth_pastell)

            ID_FLUX = "actes-reglementaires-studio"
            responseAssociationReglementaires = requests.post(
                URL_API_PASTELL + API_PASTELL_VERSION + "/entite/" + ID_E_PASTELL + "/flux/" + ID_FLUX + '/connecteur/' +
                res[
                    'id_ce'] + '/',
                data=resquest, auth=auth_pastell)

            ID_FLUX = "arretes-individuels-studio"
            responseAssociationArretes = requests.post(
                URL_API_PASTELL + API_PASTELL_VERSION + "/entite/" + ID_E_PASTELL + "/flux/" + ID_FLUX + '/connecteur/' +
                res[
                    'id_ce'] + '/',
                data=resquest, auth=auth_pastell)

            if responseAssociationDelib.ok and responseAssociationAutres.ok and responseAssociationReglementaires.ok and responseAssociationArretes.ok:
                logging.info('Association connecteur ged_megalis_opendata ok type_flux:%s, id_e:%s', ID_FLUX,
                             ID_E_PASTELL)
                return {'status': 'OK', 'message': 'Association connecteur ged_megalis_opendata ok', 'id_e': str(id_e),
                        'ID_FLUX': str(ID_FLUX)}
            else:
                logging.error('Association connecteur ged_megalis_opendata KO erreur:%s',
                              str(responseAssociationDelib.ok) + ' - ' + str(
                                  responseAssociationAutres.ok) + ' - ' + str(
                                  responseAssociationReglementaires.ok) + ' - ' + str(responseAssociationArretes.ok))

        else:
            logging.error('Creation config connecteur  ged_megalis_opendata  KO erreur:%s', responseConnecteur.text)
    else:
        logging.error('Creation connecteur  ged_megalis_opendata  KO erreur:%s', response.text)

    return {'status': 'KO', 'message': 'Association connecteur  ged_megalis_opendata  KO', 'id_e': str(id_e),
            'ID_FLUX': str(ID_FLUX)}
