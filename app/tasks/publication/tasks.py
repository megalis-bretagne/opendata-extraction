from pathlib import Path
from typing import Optional
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

from app.shared.datastructures import MetadataPastell
import app.shared.workdir_utils as workdir_utils

from app.tasks.utils import solr_connexion

from .functions import ( 
    init_publication,insert_solr,
    lien_symbolique,
    insere_nouveau_parametrage,
    _archives_current,
    _erreurs_root, 
)
from .inzipfileparser import InZipFileParser
from . import logger

celery = celeryapp.celery

@celery.task(name='creation_publication_task')
def creation_publication_task(zip_path):

    task_id: str = celery.current_task.request.id # type: ignore 
    in_zip_p = Path(zip_path)
    archive_fp, erreur_fp = _archive_et_erreurs_fullpath(task_id)

    initial_archive_fp = archive_fp
    shutil.copy(in_zip_p, initial_archive_fp)

    try:
        parsed = InZipFileParser.from_pastell_ged(zip_path)
        in_zip_p = parsed.path
        id_d = parsed.id_d()

        archive_fp, erreur_fp = _archive_et_erreurs_fullpath(task_id, id_d)
        shutil.move(initial_archive_fp, archive_fp)

        workdir_str = workdir_utils.clear_persistent_workdir()

        workdir_p = Path(workdir_str)
        workdir_zip_p = workdir_p / f"{id_d}-{task_id}.zip"

        shutil.move(in_zip_p, workdir_zip_p)

        with ZipFile(workdir_zip_p, 'r') as zipObj:
            zipObj.extractall(workdir_p)

        with (workdir_p / 'metadata.json').open('r') as f:
            metadata = json.load(f)

        metadataPastell = MetadataPastell.parse(metadata)
        newPublication = init_publication(metadataPastell.sanitize_for_db(), id_d)

    except Exception as e:
        if in_zip_p.is_file():
            in_zip_p.unlink()
        shutil.copyfile(archive_fp, erreur_fp)
        raise e


    insere_nouveau_parametrage(newPublication.siren)

    insert_solr(newPublication, est_publie=False)

    if metadataPastell.publication_open_data == '3': 
        newPublication.etat = 2 # état de la publication à 'en cours'
        db_sess = db.session
        db_sess.add(newPublication)
        task = publier_acte_task.delay(newPublication.id)
        return {'status': 'OK', 'message': 'tache de publication demandée', 'publication_id': newPublication.id,
                'task_id': str(task)}
    else:
        return {'status': 'OK', 'message': 'Acte non publié',
                'publication_open_data': str(metadataPastell.publication_open_data),
                'nature': str(metadataPastell.acte_nature)}

def _archive_et_erreurs_fullpath(task_id: str, id_d: Optional[str] = None):
    archives_dir = _archives_current()
    erreurs_dir = _erreurs_root()

    if id_d is not None:
        filename = f"{id_d}-{task_id}.zip"
    else:
        filename = f"{task_id}.zip"

    return archives_dir / filename, erreurs_dir / filename

@celery.task(name='modifier_acte_task')
def modifier_acte_task(idPublication):
    # on récupère la publication à publier en BDD
    publication = Publication.query.filter(Publication.id == idPublication).one()
    solr = solr_connexion()
    try:
        result = solr.search(q='publication_id : ' + str(idPublication), sort='id ASC', cursorMark="*")
        for doc_res in result:
            doc_res['description'][0] = publication.objet
            solr.add(doc_res)

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
        result = solr.search(q='publication_id : ' + str(idPublication), sort='id ASC', cursorMark="*")
        for doc_res in result:
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
            result = solr.search(q='publication_id : ' + str(idPublication), sort='id ASC', cursorMark="*")
            for doc_res in result:
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
        result = solr.search(q='publication_id : ' + str(idPublication), sort='id ASC', cursorMark="*")
        for doc_res in result:
            parseResult = urllib.parse.urlparse(str(doc_res['filepath'][0]))
            doc_res['est_publie'][0] = False
            try:
                os.remove(current_app.config['DIR_ROOT_PUBLICATION'] + parseResult.path)
            except FileNotFoundError as e:
                logger.info("fichier deja supprimé:" + current_app.config['DIR_ROOT_PUBLICATION'] + parseResult.path)
            solr.add(doc_res)

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


@celery.task(name='depublier_all_acte_nonpublie_task')
def depublier_all_acte_nonpublie_task():
    db_sess = db.session
    # etat =3: en - erreur
    #on recherche les actes qui sont a l'état non publié en bdd
    liste_publication = Publication.query.filter(Publication.etat == 0)
    for publication in liste_publication:
        depublier_acte_task.delay(publication.id)
    return {'status': 'OK', 'message': 'depublier_all_acte_nonpublie_task '}


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