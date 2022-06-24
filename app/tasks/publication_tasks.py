from datetime import datetime
import urllib
from zipfile import ZipFile
from sqlalchemy.exc import NoResultFound, MultipleResultsFound
from app import celeryapp
from app import celeryapp
import json
from app.models.parametrage_model import Parametrage
from app.tasks.utils import *
import hashlib
from app import db
from app.models.publication_model import Publication, Acte, PieceJointe
from lxml import etree

celery = celeryapp.celery


# TASKS
@celery.task(name='creation_publication_task')
def creation_publication_task(zip_path):
    clear_wordir()
    # on archive le fichier reçu depuis pastell (zip
    shutil.copy(zip_path, current_app.config['DIRECTORY_TO_WATCH_ARCHIVE'])

    PATH_FILE = zip_path
    WORKDIR = clear_wordir()

    # move file to workdir
    shutil.move(PATH_FILE, WORKDIR + 'objet.zip')

    # unzip file
    with ZipFile(WORKDIR + 'objet.zip', 'r') as zipObj:
        # Extract all the contents of zip file in different directory
        zipObj.extractall(WORKDIR)

    # lecture du fichier metadata.json
    with open(WORKDIR + 'metadata.json') as f:
        metadata = json.load(f)

    try:
        metadataPastell = MetadataPastell(metadata)
        # init publication table
        newPublication = init_publication(metadataPastell)
    except Exception as e:
        shutil.move(WORKDIR + 'objet.zip', current_app.config['DIRECTORY_TO_WATCH_ERREURS'])
        return {'status': 'KO', 'message': 'Metada incomplete', 'Erreur': print(e)}

    # check and init parametrage
    try:
        Parametrage.query.filter(Parametrage.siren == newPublication.siren).one()
    except MultipleResultsFound as e:
        # todo delete puis recreer le parametrage
        shutil.move(WORKDIR + 'objet.zip', current_app.config['DIRECTORY_TO_WATCH_ERREURS'])
        return {'status': 'KO', 'message': 'probleme parametrage', 'siren': newPublication.siren}

    except NoResultFound as e:
        db_sess = db.session
        newParametrage = Parametrage(created_at=datetime.now(),
                                     modified_at=datetime.now(),
                                     siren=newPublication.siren,
                                     open_data_active=True,
                                     publication_data_gouv_active=False,
                                     publication_udata_active=False)
        db_sess.add(newParametrage)
        db_sess.commit()

    # init des documents dans solr avec est_publie=False
    insert_solr(newPublication)

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
        return {'status': 'KO', 'message': 'Probleme accès à solr',
                'publication id': publication.id}

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
    except Exception as e:
        result = 0

    if not reindexationSolr:
        publication.date_publication = datetime.now()

    if (result != 0 and len(result.docs) > 0):
        lien_symbolique_et_etat_solr(publication)
    else:
        insert_solr(publication)
        try:
            result = solr.search(q='publication_id : ' + str(idPublication))
            lien_symbolique_et_etat_solr(publication, reindexationSolr)
        except Exception as e:
            result = 0

        if (result != 0 and len(result.docs) > 0):
            lien_symbolique_et_etat_solr(publication)
        else:
            # Mise à jour de la publication à erreur
            db_sess = db.session
            publication = Publication.query.filter(Publication.id == idPublication).one()
            db_sess.add(publication)
            # 1 => publie, 0:non, 2:en-cours,3:en-erreur
            publication.etat = 3
            publication.modified_at = datetime.now()
            db_sess.commit()
            return {'status': 'KO', 'message': 'pas de document dans solr',
                    'publication id': publication.id}

    # Mise à jour de la publication
    if not reindexationSolr:
        db_sess = db.session
        publication = Publication.query.filter(Publication.id == idPublication).one()
        db_sess.add(publication)
        # 1 => publie, 0:non, 2:en-cours,3:en-erreur
        publication.etat = 1
        publication.modified_at = datetime.now()
        db_sess.commit()
        return {'status': 'OK', 'message': 'publication open data réalisé',
            'publication id': publication.id}
    else:
        return {'status': 'OK', 'message': 'publication open data réalisé (moder eindexationSolr) ',
            'publication id': publication.id}


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
                logging.info("fichier deja supprimé:" + current_app.config['DIR_ROOT_PUBLICATION'] + parseResult.path)

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
    result = solr.search(q='siren : ' + str(siren))
    for doc_res in result.docs:
        doc_res['opendata_active'][0] = opendata_active
    solr.add(result.docs)

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


# @celery.task(name='indexer_publication_task')
# def indexer_publication_task(idPublication):
#     """Permet d'indexer un publication dans sol
#
#     Parameters:
#     idPublication (int): identifiant de la
#
#     Returns:
#     int:Returning value
#
#    """


# FONCTION
def insert_solr(publication):
    # infoEtablissement = api_insee_call(publication.siren)

    # Pour tous les actes ( documents lié à la publication)
    for acte in publication.actes:

        if acte.hash is None:
            acte.hash = get_hash(acte.path)
            db.session.add(acte)

        try:
            params = traiter_actes(publication, acte, isPj=False)
            # insert dans apache solr
            index_file_in_solr(acte.path, params)

        except Exception as e:
            db_sess = db.session
            publication.etat = '3'
            db_sess.add(publication)
            db_sess.commit()
            logging.exception("Erreur lors de la publication de l'acte: %s" % acte)
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
                index_file_in_solr(pj.path, params)

            except pysolr.SolrError as e:
                logging.exception("fichier ignore : %s" % pj)

    except Exception as e:
        logging.exception("probleme traitement PJ : on ignore")


def lien_symbolique_et_etat_solr(publication, reindexationSolr=False):
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
    elif publication.acte_nature == "6":
        dossier = publication.siren + os.path.sep + "Autres"

    if publication.date_budget:
        annee = publication.date_budget
    else:
        annee = str(publication.date_de_lacte.year)

    # copy de l'acte dans le dossier marque blanche
    for acte in publication.actes:
        extension = str('.' + acte.name.split(".")[-1])
        symlink_file(acte.path,
                     current_app.config['DIR_MARQUE_BLANCHE'] + dossier + os.path.sep + annee + os.path.sep,
                     acte.hash + extension)

    # copy des pj dans le dossier marque blanche
    for pj in publication.pieces_jointe:
        extension = str('.' + pj.name.split(".")[-1])
        symlink_file(pj.path,
                     current_app.config['DIR_MARQUE_BLANCHE'] + dossier + os.path.sep + annee + os.path.sep,
                     pj.name + extension)

    solr = solr_connexion()
    result = solr.search(q='publication_id : ' + str(publication.id))
    # Mise à jour dans Solr
    for doc_res in result.docs:
        if reindexationSolr:
            doc_res['est_publie'][0] = publication.etat
        else:
            doc_res['est_publie'][0] = True
        if 'date_de_publication' in doc_res:
            doc_res['date_de_publication'][0] = publication.date_publication.strftime("%Y-%m-%dT%H:%M:%SZ")
    solr.add(result.docs)


def traiter_actes(publication, acte, isPj):
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
    elif publication.acte_nature == "6":
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
    symlink_file(acte.path, current_app.config['DIR_MARQUE_BLANCHE'] + dossier + os.path.sep + annee + os.path.sep,
                 acte.hash + extension)
    return data


def init_document(data, acte, parametrage, publication, urlPDF, typology):

    # data["literal.hash"] = '9ebbd0b25760557393a43064a92bae539d96210'
    # data["literal.publication_id"] = 123
    # data["literal.filepath"] = "https://data-preprod.megalis.bretagne.bzh/OpenData/253514491/Budget/2020/e5753a1c860c06fb54fbf45d456f597f3a4b4613e8f825a8c027b91df10ea8d2.pdf"
    # data["literal.est_publie"] = True
    # data["literal.opendata_active"] = True
    # data["literal.date_budget"] = "2022"
    # now = datetime.now()
    # data["literal.date"] = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    # data["literal.date_de_publication"] = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    # data["literal.description"] = 'publication.objet'
    # data["literal.documentidentifier"] = 'DELIB_TEST'
    # data["literal.documenttype"] = 1
    # data["literal.classification"] = "7.1 Finances locales/Divers"
    # data["literal.classification_code"] = "7.1"
    # data["literal.classification_nom"] = 'Finances locales/Divers'
    # data["literal.typology"] = "99_DE"
    # data["literal.siren"] = "242900710"

    data["commit"] = 'true'
    data["literal.hash"] = acte.hash
    data["literal.publication_id"] = publication.id
    data["literal.filepath"] = urlPDF
    # data["literal.stream_content_type"] = data['metadata']["Content-Type"]
    # etat publication
    data["literal.est_publie"] = True
    data["literal.opendata_active"] = parametrage.open_data_active
    data["literal.date_budget"] = publication.date_budget

    # partie métadata (issu du fichier metadata.json de pastell)
    data["literal.date"] = publication.date_de_lacte.strftime("%Y-%m-%dT%H:%M:%SZ")
    now = datetime.now()  # current date and time
    data["literal.date_de_publication"] = now.strftime("%Y-%m-%dT%H:%M:%SZ")

    data["literal.description"] = publication.objet
    data["literal.documentidentifier"] = publication.numero_de_lacte
    data["literal.documenttype"] = publication.acte_nature
    data["literal.classification"] = publication.classification_code + " " + publication.classification_nom,
    data["literal.classification_code"] = publication.classification_code,
    data["literal.classification_nom"] = publication.classification_nom,
    data["literal.typology"] = typology,
    # PARTIE RESULT API SIRENE
    data["literal.siren"] = publication.siren


def init_publication(metadataPastell):
    WORKDIR = get_or_create_workdir()
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
        envoi_depot=metadataPastell.envoi_depot
    )
    db_sess.add(newPublication)
    db_sess.commit()

    annee = str(newPublication.date_de_lacte.year)

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
    elif newPublication.acte_nature == "6":
        dossier = newPublication.siren + os.path.sep + "Autres"
        urlPub = newPublication.siren + '/' + "Autres"

    contient_acte_tamponne = False
    for acte_tamponne in metadataPastell.liste_acte_tamponne:
        dossier_publication = current_app.config['DIR_PUBLICATION'] + dossier + os.path.sep + annee + os.path.sep

        path = WORKDIR + acte_tamponne
        format = str('.' + acte_tamponne.split(".")[-1])
        hash = get_hash(path)

        newDoc = Acte(
            name=acte_tamponne,
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
            newDoc = Acte(
                name=arrete,
                publication_id=newPublication.id,
                url=current_app.config['URL_PUBLICATION'] + urlPub + '/' + annee + '/' + hash + format,
                path=dossier_publication + hash + format,
                hash=hash
            )
            db_sess.add(newDoc)
            move_file(path, dossier_publication, hash + format)
    # Pour tous les fichiers pj présents dans le zip
    if metadataPastell.liste_autre_document_attache is not None:
        for pj in metadataPastell.liste_autre_document_attache:
            dossier_publication = current_app.config['DIR_PUBLICATION'] + dossier + os.path.sep + annee + os.path.sep
            path = WORKDIR + pj
            format = str('.' + pj.split(".")[-1])
            hash = get_hash(path)

            newPj = PieceJointe(
                name=pj,
                url=current_app.config[
                        'URL_PUBLICATION'] + urlPub + '/' + annee + '/' + hash + format,
                path=dossier_publication + hash + format,
                hash=hash,
                publication_id=newPublication.id
            )
            db_sess.add(newPj)
            move_file(path, dossier_publication, hash + format)
    db_sess.commit()
    return newPublication


class MetadataPastell:
    def __init__(self, metajson):
        self.numero_de_lacte = metajson['numero_de_lacte']
        self.date_de_lacte = metajson['date_de_lacte']
        self.objet = metajson['objet']
        self.siren = metajson['siren']
        self.acte_nature = metajson['acte_nature']


        if 'envoi_depot' in metajson:
            self.envoi_depot = metajson['envoi_depot']
        else:
            self.envoi_depot = 'checked'

        # liste de fichier arrete
        self.liste_arrete = metajson['arrete']
        # liste de fichier arrete tamponne
        if 'acte_tamponne' in metajson:
            self.liste_acte_tamponne = metajson['acte_tamponne']
        else:
            self.liste_acte_tamponne = []

        # liste de d'annexe
        if 'autre_document_attache' in metajson:
            self.liste_autre_document_attache = metajson['autre_document_attache']
        else:
            self.liste_autre_document_attache = []

        if 'type_piece' in metajson:
            self.type_piece = metajson['type_piece']
        else:
            self.type_piece = ''


        if 'classification' in metajson:
            self.classification = metajson['classification']
        else:
            self.classification = ''


        if 'publication_open_data' in metajson:
            if len(metajson['publication_open_data']) == 0:
                # valeur par défaut si dans le fichier metadata publication_open_data n'est pas présent
                if self.acte_nature == '1' or self.acte_nature == '2' or self.acte_nature == '5':
                    # délib, actes réglementaires et budget oui par defaut
                    self.publication_open_data = '3'
                elif self.acte_nature == '3' or self.acte_nature == '6':
                    # actes individuels et autres non par defaut
                    self.publication_open_data = '1'
                else:
                    # le reste à ne sais pas
                    self.publication_open_data = '2'
            else:
                self.publication_open_data = metajson['publication_open_data']
        else:
            # valeur par défaut si dans le fichier metadata publication_open_data n'est pas présent
            if self.acte_nature == '1' or self.acte_nature == '2' or self.acte_nature == '5':
                # délib, actes réglementaires et budget oui par defaut
                self.publication_open_data = '3'
            elif self.acte_nature == '3' or self.acte_nature == '6':
                # actes individuels et autres non par defaut
                self.publication_open_data = '1'
            else:
                # le reste à ne sais pas
                self.publication_open_data = '2'

        x = self.classification.split(" ", 1)
        # valeur par defaut
        self.classification_code = "6"
        if len(x) == 2:
            self.classification_code = x[0]
        elif len(x) == 1:
            self.classification_code = x[0]

        classification_code_split = self.classification_code.split(".", -1)
        if len(classification_code_split) > 2:
            self.classification_nom = classification_actes_dict[
                float(classification_code_split[0] + '.' + classification_code_split[1])]
        else:
            self.classification_nom = classification_actes_dict[float(self.classification_code)]


def __get_date_buget(xml_file: str):
    namespaces = {'nms': 'http://www.minefi.gouv.fr/cp/demat/docbudgetaire'}

    tree = etree.parse(xml_file)
    annee = tree.findall('/nms:Budget/nms:BlocBudget/nms:Exer', namespaces)[0].attrib.get('V')
    return annee
