import os
import pytz
from pathlib import Path
import pysolr
from lxml import etree
from datetime import datetime
from datetime import timedelta

from sqlalchemy.exc import IntegrityError

from flask import current_app
from app import db

from app.models.publication_model import Publication,Acte,PieceJointe
from app.models.parametrage_model import Parametrage

from app.tasks.utils import get_hash,index_file_in_solr,symlink_file,unsymlink_file,move_file
from app.shared.client_api_sirene.flask_functions import etablissement_siege_pour_siren
import app.shared.workdir_utils as workdir_utils

from . import logger

def insert_solr(publication: Publication, est_publie, est_dans_blockchain=False, blockchain_tx=''):
    # Pour tous les actes ( documents lié à la publication)
    for acte in publication.actes:

        if acte.hash is None:
            acte.hash = get_hash(acte.path)
            db.session.add(acte)

        try:
            params = traiter_actes(publication, acte, isPj=False)
            # insert dans apache solr
            params["literal.est_publie"] = est_publie
            if est_dans_blockchain:
                params["literal.blockchain_enable"] = True
                params["literal.blockchain_transaction"] = str(blockchain_tx)
                params["literal.blockchain_url"] = current_app.config['BLOCKCHAIN_EXPLORER'] + str(blockchain_tx)

            index_file_in_solr(acte.path, params)
        except Exception as e:
            db_sess = db.session
            publication.etat = '3'
            db_sess.add(publication)
            db_sess.commit()
            logger.exception("Erreur lors de la publication de l'acte: %s" % acte)
            raise e

    # Pour tous les fichiers pj présents dans le zip
    try:
        for pj in publication.pieces_jointe:

            if pj.hash is None:
                pj.hash = get_hash(pj.path)
                db.session.add(pj)
            try:
                params = traiter_actes(publication, pj, isPj=True)
                # insert dans apache solr
                params["literal.est_publie"] = est_publie and pj.publie
                index_file_in_solr(pj.path, params)

            except pysolr.SolrError as e:
                logger.exception("fichier ignore : %s" % pj)

    except Exception as e:
        logger.exception("probleme traitement PJ : on ignore")


# TODO: plus utilisé ?! à verifier avec Yann
def lien_symbolique(publication):
    if publication.acte_nature == "1":
        dossier = publication.siren + os.path.sep + "Deliberation"
    elif publication.acte_nature == "2":
        dossier = publication.siren + os.path.sep + "Actes_reglementaires"
    elif publication.acte_nature == "3":
        dossier = publication.siren + os.path.sep + "Actes_individuels"
    elif publication.acte_nature == "4":
        dossier = publication.siren + os.path.sep + "Contrats_conventions_avenants"
    elif publication.acte_nature == "5":
        dossier = publication.siren + os.path.sep + "Budget"
    elif publication.acte_nature == "7":
        dossier = publication.siren + os.path.sep + "Hors_prefecture"
    else:
        #cas par defaut et acte_nature=6
        dossier = publication.siren + os.path.sep + "Autres"

    if publication.date_budget:
        annee = publication.date_budget
    else:
        annee = str(publication.date_de_lacte.year)

    def _symlink(acte: Acte | PieceJointe, filename):
        extension = str('.' + acte.name.split(".")[-1])
        src = acte.path
        dest_dir = current_app.config['DIR_MARQUE_BLANCHE'] + dossier + os.path.sep + annee + os.path.sep
        name = filename + extension
        symlink_file(src, dest_dir, name)

    # copy de l'acte dans le dossier marque blanche
    for acte in publication.actes:
        _symlink(acte, acte.hash)
    # copy des pj dans le dossier marque blanche
    for pj in publication.pieces_jointe:
        _symlink(pj, pj.name)

def traiter_actes(publication: Publication, acte: Acte | PieceJointe, isPj: bool):

    if publication.date_budget:
        annee = publication.date_budget
    else:
        annee = str(publication.date_de_lacte.year)
    parametrage = Parametrage.query.filter(Parametrage.siren == publication.siren).one()

    if publication.acte_nature == "1":
        dossier = publication.siren + os.path.sep + "Deliberation"
        typology = "99_DE"
    elif publication.acte_nature == "2":
        dossier = publication.siren + os.path.sep + "Actes_reglementaires"
        typology = "99_AT"
    elif publication.acte_nature == "3":
        dossier = publication.siren + os.path.sep + "Actes_individuels"
        typology = "99_AI"
    elif publication.acte_nature == "4":
        dossier = publication.siren + os.path.sep + "Contrats_conventions_avenants"
        typology = "99_CO"
    elif publication.acte_nature == "5":
        dossier = publication.siren + os.path.sep + "Budget"
        typology = "99_BU"
    elif publication.acte_nature == "7":
        dossier = publication.siren + os.path.sep + "Hors_prefecture"
        typology = "99_HP"
    else:
        # cas par defaut et acte_nature=6
        dossier = publication.siren + os.path.sep + "Autres"
        typology = "99_AU"

    if isPj == True:
        typology = "PJ"

    extension = str('.' + acte.name.split(".")[-1])
    urlPDF = current_app.config['URL_MARQUE_BLANCHE'] + dossier + "/" + annee + "/" + acte.hash + extension

    data = {}
    # initialisation du document apache solr
    init_document(data, acte, parametrage, publication, urlPDF, typology)

    # dépot dans le serveur
    pj: PieceJointe = acte if (isPj) else None # type: ignore
    dest_dir = current_app.config['DIR_MARQUE_BLANCHE'] + dossier + os.path.sep + annee + os.path.sep
    dest_filename = acte.hash + extension
    if pj is None or pj.publie:
        symlink_file(acte.path, dest_dir, dest_filename)
    else:
        unsymlink_file(dest_dir, dest_filename)
    return data

def init_document(data, acte, parametrage, publication, urlPDF, typology):
    data["commit"] = 'true'
    data["literal.hash"] = acte.hash
    data["literal.publication_id"] = publication.id
    data["literal.filepath"] = urlPDF
    # # etat publication
    # data["literal.est_publie"] = False
    data["literal.opendata_active"] = parametrage.open_data_active
    data["literal.date_budget"] = publication.date_budget
    # partie métadata (issu du fichier metadata.json de pastell)
    data["literal.date"] = publication.date_de_lacte.strftime("%Y-%m-%dT%H:%M:%SZ")

    date_publication = publication.date_publication
    if publication.date_publication is not None:
        # on ajoute 10s à la date_de_publication des PJ pour pouvoir utiliser ce critère pour le tri
        if typology == "PJ":
            date_publication = date_publication + timedelta(seconds=10)
        dt_str = date_publication.astimezone(pytz.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        data["literal.date_de_publication"] = dt_str

    data["literal.description"] = publication.objet
    data["literal.nature_autre_detail"] = publication.nature_autre_detail
    data["literal.documentidentifier"] = publication.numero_de_lacte
    data["literal.documenttype"] = _documenttype(publication)
    data["literal.classification"] = publication.classification_code + " " + publication.classification_nom,
    data["literal.classification_code"] = publication.classification_code,
    data["literal.classification_nom"] = publication.classification_nom,
    data["literal.typology"] = typology,
    # PARTIE RESULT API SIRENE
    data["literal.siren"] = publication.siren

def _documenttype(publication: Publication):
    acte_nature = str(publication.acte_nature)
    nature_autre_detail = str(publication.nature_autre_detail)
    if acte_nature != "7": # 7 - hors prefecture
        return acte_nature
    
    # Hors prefecture
    # LD: 71 - Liste des délibérations
    # AT: 72 - Arrêté Temporaire
    # PV: 73 - Procès Verbal
    if nature_autre_detail == "LD":
        return "71"
    elif nature_autre_detail == "AT":
        return "72"
    elif nature_autre_detail == "PV":
        return "73"
    else:
        return "7"


def init_publication(metadataPastell, id_d: str):
    WORKDIR = workdir_utils.get_or_create_persistent_workdir()
    # publication open data oui par défaut 0:oui / 1:non / 2:Ne sais pas
    pub_open_data = '0'
    date_budget = None
    # SI acte BUDGET, alors on lit le fichier xml pour obtenir l'année
    if metadataPastell.acte_nature == "5":
        try:
            xml_buget = WORKDIR + metadataPastell.liste_arrete[0]
            date_budget = __get_date_buget(xml_buget)
        except Exception as e:
            # probleme de lecture du fichier XML
            # probablement pas un fichier XML
            print(e)

    db_sess = db.session
    newPublication = Publication(
        numero_de_lacte=metadataPastell.numero_de_lacte,
        objet=metadataPastell.objet,
        siren=metadataPastell.siren,
        publication_open_data=metadataPastell.publication_open_data,
        date_de_lacte=metadataPastell.date_de_lacte,
        created_at=datetime.now(),
        modified_at=datetime.now(),
        date_budget=date_budget,
        classification_code=metadataPastell.classification_code,
        classification_nom=metadataPastell.classification_nom,
        acte_nature=metadataPastell.acte_nature,
        envoi_depot=metadataPastell.envoi_depot,
        nature_autre_detail=metadataPastell.nature_autre_detail,
        pastell_id_d=id_d,
    )
    db_sess.add(newPublication)
    db_sess.commit()

    # XXX: retour de db, le type dt est ici une datetime
    date_de_lacte_dt: datetime = newPublication.date_de_lacte # type: ignore 
    annee = str(date_de_lacte_dt.year)

    if newPublication.acte_nature == "1":
        dossier = newPublication.siren + os.path.sep + "Deliberation"
        urlPub = newPublication.siren + '/' + "Deliberation"
    elif newPublication.acte_nature == "2":
        dossier = newPublication.siren + os.path.sep + "Actes_reglementaires"
        urlPub = newPublication.siren + '/' + "Actes_reglementaires"
    elif newPublication.acte_nature == "3":
        dossier = newPublication.siren + os.path.sep + "Actes_individuels"
        urlPub = newPublication.siren + '/' + "Actes_individuels"
    elif newPublication.acte_nature == "4":
        dossier = newPublication.siren + os.path.sep + "Contrats_conventions_avenants"
        urlPub = newPublication.siren + '/' + "Contrats_conventions_avenants"
    elif newPublication.acte_nature == "5":
        dossier = newPublication.siren + os.path.sep + "Budget"
        urlPub = newPublication.siren + '/' + "Budget"
    elif newPublication.acte_nature == "7":
        dossier = newPublication.siren + os.path.sep + "Hors_prefecture"
        urlPub = newPublication.siren + '/' + "Hors_prefecture"
    else:
        #cas par defaut et acte_nature=6
        dossier = newPublication.siren + os.path.sep + "Autres"
        urlPub = newPublication.siren + '/' + "Autres"

    contient_acte_tamponne = False
    for acte_tamponne in metadataPastell.liste_acte_tamponne:
        dossier_publication = current_app.config['DIR_PUBLICATION'] + dossier + os.path.sep + annee + os.path.sep

        path = WORKDIR + acte_tamponne
        format = str('.' + acte_tamponne.split(".")[-1])
        hash = get_hash(path)
        #encode('latin-1','ignore').decode('latin-1', 'ignore')
        #pour ne pas faire planter la bdd qui est encodée en latin-1
        newDoc = Acte(
            name=acte_tamponne.encode('latin-1','ignore').decode('latin-1', 'ignore'),
            publication_id=newPublication.id,
            url=current_app.config['URL_PUBLICATION'] + urlPub + '/' + annee + '/' + hash + format,
            path=dossier_publication + hash + format,
            hash=hash
        )
        db_sess.add(newDoc)
        move_file(path, dossier_publication, hash + format)
        contient_acte_tamponne = True

    # si on a pas d'acte tamponne on prend le fichier non tamponné
    if contient_acte_tamponne is False:
        for arrete in metadataPastell.liste_arrete:
            dossier_publication = current_app.config['DIR_PUBLICATION'] + dossier + os.path.sep + annee + os.path.sep
            path = WORKDIR + arrete
            format = str('.' + arrete.split(".")[-1])
            hash = get_hash(path)
            # encode('latin-1','ignore').decode('latin-1', 'ignore')
            # pour ne pas faire planter la bdd qui est encodée en latin-1
            newDoc = Acte(
                name=arrete.encode('latin-1','ignore').decode('latin-1', 'ignore'),
                publication_id=newPublication.id,
                url=current_app.config['URL_PUBLICATION'] + urlPub + '/' + annee + '/' + hash + format,
                path=dossier_publication + hash + format,
                hash=hash
            )
            db_sess.add(newDoc)
            move_file(path, dossier_publication, hash + format)

    try :
        # Pour tous les fichiers pj présents dans le zip
        if metadataPastell.liste_autre_document_attache is not None:
            for pj in metadataPastell.liste_autre_document_attache:
                dossier_publication = current_app.config['DIR_PUBLICATION'] + dossier + os.path.sep + annee + os.path.sep
                path = WORKDIR + pj
                format = str('.' + pj.split(".")[-1])
                hash = get_hash(path)
                # encode('latin-1','ignore').decode('latin-1', 'ignore')
                # pour ne pas faire planter la bdd qui est encodée en latin-1
                newPj = PieceJointe(
                    name=pj.encode('latin-1','ignore').decode('latin-1', 'ignore'),
                    url=current_app.config[
                            'URL_PUBLICATION'] + urlPub + '/' + annee + '/' + hash + format,
                    path=dossier_publication + hash + format,
                    hash=hash,
                    publication_id=newPublication.id
                )
                move_file(path, dossier_publication, hash + format)
                db_sess.add(newPj)

    except Exception as e:
        print("Problème de création de la PJ, on ignore")
        logger.exception(e)

    db_sess.commit()
    return newPublication

def insere_nouveau_parametrage(siren: str):
    """Pour le siren donné insère le paramétrage d'initialisation par défaut."""
    parametrage = Parametrage.query.filter(Parametrage.siren == siren).first()
    if parametrage is None:
        db_sess = db.session
        try:
            nic = "00000"
            denomination = ""

            try:
                etab_siege = etablissement_siege_pour_siren(siren)
                nic = etab_siege.nic
                denomination = etab_siege.denomination_unite_legale
            except Exception as err:
                logger.warning(f"Impossible de récupérer l'établissement siège. Le paramétrage sera incomplet")
                logger.warning("Exception:")
                logger.exception(err)

            new_parametrage = Parametrage(created_at=datetime.now(),
                                          modified_at=datetime.now(),
                                          siren=siren,
                                          nic=nic,
                                          denomination=denomination,
                                          open_data_active=True,
                                          publication_data_gouv_active=False,
                                          publication_udata_active=False)
            db_sess.add(new_parametrage)
            db_sess.commit()

        except IntegrityError:
            # Un autre worker a déjà inséré le paramétrage.
            db_sess.rollback()

def __get_date_buget(xml_file: str):
    namespaces = {'nms': 'http://www.minefi.gouv.fr/cp/demat/docbudgetaire'}

    tree = etree.parse(xml_file)
    annee = tree.findall('/nms:Budget/nms:BlocBudget/nms:Exer', namespaces)[0].attrib.get('V')
    return annee


def _archives_root() -> Path:
    """Retourne la racine des dossiers archive"""
    archives_dir_str = current_app.config["DIRECTORY_TO_WATCH_ARCHIVE"]
    return Path(archives_dir_str)


def _archives_current() -> Path:
    """
    Crée et/ou retourne le dossier d'archives courant (suivant la date de reception)
    e.g: watcher/archives/2022/12/10
    """
    y = datetime.now().year
    m = datetime.now().month
    d = datetime.now().day

    p = _archives_root() / str(y) / str(m) / str(d)

    os.makedirs(str(p), exist_ok=True)

    return p

def _erreurs_root() -> Path:
    """Retourne le dossier watcher/erreurs"""
    erreurs_dir_str = current_app.config['DIRECTORY_TO_WATCH_ERREURS']
    return Path(erreurs_dir_str)