import urllib
import more_itertools
import json
from zipfile import ZipFile
import shutil
import os
from datetime import datetime

from flask import current_app
from app import celeryapp
from app import db

from app.models.publication_model import Publication
from app.models.parametrage_model import Parametrage

from app.shared.client_api_sirene.flask_functions import etablissement_siege_pour_siren
from app.shared.datastructures import MetadataPastell
import app.shared.workdir_utils as workdir_utils

from app.tasks.utils import solr_connexion

from .functions import init_publication,insert_solr,lien_symbolique,insere_nouveau_parametrage
from . import logger

celery = celeryapp.celery

@celery.task(name='creation_publication_task')
def creation_publication_task(zip_path):
    # on archive le fichier reçu depuis pastell (zip
    shutil.copy(zip_path, current_app.config['DIRECTORY_TO_WATCH_ARCHIVE'])

    PATH_FILE = zip_path
    WORKDIR = workdir_utils.clear_persistent_workdir()

    # move file to workdir
    shutil.move(PATH_FILE, WORKDIR + 'objet.zip')

    try:
        # unzip file
        with ZipFile(WORKDIR + 'objet.zip', 'r') as zipObj:
            # Extract all the contents of zip file in different directory
            zipObj.extractall(WORKDIR)

        # lecture du fichier metadata.json
        with open(WORKDIR + 'metadata.json') as f:
            metadata = json.load(f)

        metadataPastell = MetadataPastell.parse(metadata)

    except Exception as e:
        strDate = datetime.now().strftime('%Y-%m-%d-%H%M%S')
        shutil.move(WORKDIR + 'objet.zip',
                    current_app.config['DIRECTORY_TO_WATCH_ERREURS'] + '/pastell_' + strDate + '.zip')
        raise e

    try:
        # init publication table
        newPublication = init_publication(metadataPastell.sanitize_for_db())
    except Exception as e:
        strDate = datetime.now().strftime('%Y-%m-%d-%H%M%S')
        shutil.move(WORKDIR + 'objet.zip',
                    current_app.config['DIRECTORY_TO_WATCH_ERREURS'] + '/pastell_'+metadataPastell.siren+'_' + strDate + '.zip')
        raise e


    # check and init parametrage
    insere_nouveau_parametrage(newPublication.siren)

    # init des documents dans solr avec est_publie=False
    insert_solr(newPublication, est_publie=False)

    # creation de la tache de publication openData et on passe l'état de la publication à en cours
    if metadataPastell.publication_open_data == '3':
        newPublication.etat = 2
        db_sess = db.session
        db_sess.add(newPublication)
        task = publier_acte_task.delay(newPublication.id)
        return {'status': 'OK', 'message': 'tache de publication demandée', 'publication_id': newPublication.id,
                'task_id': str(task)}
    else:
        return {'status': 'OK', 'message': 'Acte non publié',
                'publication_open_data': str(metadataPastell.publication_open_data),
                'nature': str(metadataPastell.acte_nature)}


@celery.task(name='modifier_acte_task')
def modifier_acte_task(idPublication):
    # on récupère la publication à publier en BDD
    publication = Publication.query.filter(Publication.id == idPublication).one()
    solr = solr_connexion()

    try:
        result = solr.search(q='publication_id : ' + str(idPublication))

        if (result != 0 and len(result.docs) > 0):
            # Mise à jour dans Solr
            for doc_res in result.docs:
                doc_res['description'][0] = publication.objet
            solr.add(result.docs)
            return {'status': 'OK', 'message': 'modification acte réalisée',
                    'publication id': publication.id}
    except Exception as e:
        raise e

    return {'status': 'OK', 'message': 'Aucun document solr à modifier',
            'publication id': publication.id}


@celery.task(name='publier_acte_task')
def publier_acte_task(idPublication, reindexationSolr=False):
    # on récupère la publication à publier en BDD
    publication = Publication.query.filter(Publication.id == idPublication).one()

    if publication.est_supprime:
        return {'status': 'OK', 'message': 'publication non autorisé car supprimé colonne est_supprimé',
                'publication id': publication.id}

    # CAS d'une republication si deja présent dans solr alors on change de flag est_publié et on remets les fichiers dans le dossier marque blanche
    solr = solr_connexion()
    try:
        result = solr.search(q='publication_id : ' + str(idPublication))
        for doc_res in result.docs:
            solr.delete(doc_res['id'])
    except Exception as e:
        result = 0

    if not reindexationSolr:
        publication.date_publication = datetime.now()

    try:
        insert_solr(publication, est_publie=True)
        lien_symbolique(publication)

    except Exception as e:
        logger.exception(e)
        db_sess = db.session
        publication = Publication.query.filter(Publication.id == idPublication).one()
        db_sess.add(publication)
        # 1 => publie, 0:non, 2:en-cours,3:en-erreur
        publication.etat = 3
        publication.modified_at = datetime.now()
        db_sess.commit()
        raise e

    # Mise à jour de la publication
    if not reindexationSolr:
        db_sess = db.session
        publication = Publication.query.filter(Publication.id == idPublication).one()
        db_sess.add(publication)
        # 1 => publie, 0:non, 2:en-cours,3:en-erreur
        publication.etat = 1
        publication.modified_at = datetime.now()
        db_sess.commit()

        if current_app.config['USE_BLOCKCHAIN']:
            publier_blockchain_task.delay(publication.id)

        return {'status': 'OK', 'message': 'publication open data réalisé',
                'publication id': publication.id}
    else:
        return {'status': 'OK', 'message': 'publication open data réalisé (moder eindexationSolr) ',
                'publication id': publication.id}


@celery.task(name='publier_blockchain_task')
def publier_blockchain_task(idPublication):
    from web3 import Web3
    from web3.middleware import geth_poa_middleware

    contract_address = current_app.config['CONTRACT_ADDRESS']

    account_from = {
        'private_key': current_app.config['PRIVATE_KEY'],
        'address': current_app.config['PUBLIC_KEY'],
    }

    abi = current_app.config['BLOCKCHAIN_ABI']

    w3 = Web3(Web3.HTTPProvider(current_app.config['HTTP_PROVIDER']))

    w3.middleware_onion.inject(geth_poa_middleware, layer=0)

    # 4. Create contract instance
    publisher = w3.eth.contract(address=contract_address, abi=abi)

    # on récupère la publication à publier en BDD
    publication = Publication.query.filter(Publication.id == idPublication).one()

    # copy de l'acte dans le dossier marque blanche
    for acte in publication.actes:
        # 5. Build increment tx
        publisher_tx = publisher.functions.publish(publication.siren, acte.url).buildTransaction(
            {
                'from': account_from['address'],
                'nonce': w3.eth.get_transaction_count(account_from['address']),
            }
        )
        # 6. Sign tx with PK
        tx_create = w3.eth.account.sign_transaction(publisher_tx, account_from['private_key'])
        # 7. Send tx and wait for receipt
        tx_hash = w3.eth.send_raw_transaction(tx_create.rawTransaction)
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

        solr = solr_connexion()
        try:
            result = solr.search(q='publication_id : ' + str(idPublication))
            for doc_res in result.docs:
                solr.delete(doc_res['id'])
        except Exception as e:
            result = 0

        insert_solr(publication, est_publie=True, est_dans_blockchain=True, blockchain_tx=tx_receipt.transactionHash.hex())

        return {'status': 'OK', 'message': 'publié sur ' + current_app.config['NETWORK_NAME'] + ' ;)',
                'tx_receipt': tx_receipt.transactionHash.hex()}

    return {'status': 'KO', 'message': 'non publié :(', }


@celery.task(name='depublier_acte_task')
def depublier_acte_task(idPublication):
    publication = Publication.query.filter(Publication.id == idPublication).one()
    if publication:
        # suppression dans solr
        solr = solr_connexion()
        result = solr.search(q='publication_id : ' + str(idPublication))

        # suppression sur le filesystem
        for doc_res in result.docs:
            parseResult = urllib.parse.urlparse(str(doc_res['filepath'][0]))
            doc_res['est_publie'][0] = False
            try:
                os.remove(current_app.config['DIR_ROOT_PUBLICATION'] + parseResult.path)
            except FileNotFoundError as e:
                logger.info("fichier deja supprimé:" + current_app.config['DIR_ROOT_PUBLICATION'] + parseResult.path)

        solr.add(result.docs)

        # Mise à jour de la publication
        db_sess = db.session
        db_sess.add(publication)
        # 1 => publie, 0:non, 2:en-cours,3:en-erreur
        publication.etat = 0
        publication.modified_at = datetime.now()
        db_sess.commit()

    return {'status': 'OK', 'message': 'depublication open data réalisée',
            'publication id': idPublication}


@celery.task(name='gestion_activation_open_data_task')
def gestion_activation_open_data(siren, opendata_active):
    solr = solr_connexion()
    results = solr.search(q='siren : ' + str(siren), fl='*', sort='id ASC', cursorMark="*")
    chunks = more_itertools.chunked(results, 1000)

    for docs in chunks:
        for doc in docs: doc["opendata_active"][0] = opendata_active
        solr.add(docs, fieldUpdates={"opendata_active": "set"})

    if opendata_active:
        __reindexer_publications_publiees_de_siren(siren)

    return {'status': 'OK', 'message': 'mise à jour du flag opendata_active dans solr',
            'siren': siren, 'opendata_active': opendata_active}


@celery.task(name='republier_all_acte_task')
def republier_all_acte_task(etat):
    db_sess = db.session
    # etat =3: en - erreur
    liste_publication = Publication.query.filter(Publication.etat == etat)
    for publication in liste_publication:
        # 1 => publie, 0:non, 2:en-cours,3:en-erreur
        # publication.etat = 2
        # db_sess.commit()
        publier_acte_task.delay(publication.id, True)
    return {'status': 'OK', 'message': 'republier_all_acte_task '}

@celery.task(name='republier_actes_pour_siren_task')
def republier_actes_pour_siren_task(siren, etat):
    ls_publications = Publication.query.filter(Publication.siren == siren, Publication.etat == etat)
    for publication in ls_publications:
        publier_acte_task.delay(publication.id, True)
    return {'status': 'OK', 'message': 'republier_actes_pour_siren_task'}


def __reindexer_publications_publiees_de_siren(siren: str):
    result = Publication.query.filter(
        Publication.siren == siren, 
        Publication.etat == 1, # 1 => publie
    )
    for publication in result:
        publier_acte_task.delay(publication.id, reindexationSolr=True)