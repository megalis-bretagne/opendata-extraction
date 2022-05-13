from datetime import datetime
import urllib
from zipfile import ZipFile
from sqlalchemy.exc import NoResultFound, MultipleResultsFound
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
    WORKDIR = get_or_create_workdir()

    # move file to workdir
    shutil.move(PATH_FILE, WORKDIR + 'objet.zip')

    # unzip file
    with ZipFile(WORKDIR + 'objet.zip', 'r') as zipObj:
        # Extract all the contents of zip file in different directory
        zipObj.extractall(WORKDIR)

    # lecture du fichier metadata.json
    with open(WORKDIR + 'metadata.json') as f:
        metadata = json.load(f)

    metadataPastell = MetadataPastell(metadata)

    # si nature de l'acte différent de délibération ou bin budget on ignore le fichier
    if metadataPastell.acte_nature != "1" and metadataPastell.acte_nature != "5":
        return {'status': 'ignore', 'message': 'nature acte différent de délibération ou budget',
                'acte_nature': str(metadataPastell.acte_nature)}

    # init publication table
    newPublication = init_publication(metadataPastell)

    # check and init parametrage
    try:
        Parametrage.query.filter(Parametrage.siren == newPublication.siren).one()
    except MultipleResultsFound as e:
        # todo delete puis recreer le parametrage
        print(e)
    except NoResultFound as e:
        db_sess = db.session
        newParametrage = Parametrage(created_at=datetime.now(),
                                     modified_at=datetime.now(),
                                     siren=newPublication.siren,
                                     open_data_active=True,
                                     publication_data_gouv_active=False,
                                     publication_udata_active=False
                                     )

        db_sess.add(newParametrage)
        db_sess.commit()

    # init des documents dans solr avec est_publie=False
    insert_solr(newPublication)

    # si acte différent de budget et publication opendata non ou ne sais pas alors on de
    if metadataPastell.acte_nature != "5":
        if metadataPastell.publication_open_data == '1' or metadataPastell.publication_open_data == '2':
            return {'status': 'ignore', 'message': 'publication open data différent de oui',
                    'publication_open_data': str(metadataPastell.publication_open_data)}

    # creation de la tache de publication openData et on passe l'état de la publication à en cours
    newPublication.etat = 2
    db_sess = db.session
    db_sess.add(newPublication)
    task = publier_acte_task.delay(newPublication.id)

    return {'status': 'OK', 'message': 'tache de publication demandée', 'publication_id': newPublication.id,
            'task_id': str(task)}


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


@celery.task(name='publier_acte_task', rate_limit='20/m')
def publier_acte_task(idPublication):
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

    if (result != 0 and len(result.docs) > 0):
        lien_symbolique_et_etat_solr(publication)
    else:
        insert_solr(publication)
        try:
            result = solr.search(q='publication_id : ' + str(idPublication))
            lien_symbolique_et_etat_solr(publication)
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
    db_sess = db.session
    publication = Publication.query.filter(Publication.id == idPublication).one()
    db_sess.add(publication)
    # 1 => publie, 0:non, 2:en-cours,3:en-erreur
    publication.etat = 1
    publication.modified_at = datetime.now()
    db_sess.commit()
    return {'status': 'OK', 'message': 'publication open data réalisé',
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
        publication.etat = 2
        db_sess.commit()
        publier_acte_task.delay(publication.id)
    return {'status': 'OK', 'message': 'republier_all_acte_task '}


# FONCTION
def insert_solr(publication):
    # call API insee v3, sur /siret avec siren en parametre + etablissementSiege=true
    result = api_insee_call(publication.siren)
    if len(result['etablissements']) > 0:
        infoEtablissement = InfoEtablissement(result['etablissements'][0])

    # Pour tous les actes ( documents lié à la publication)
    for acte in publication.actes:
        with open(acte.path, 'rb') as fh:
            try:
                solr = solr_connexion()
                data = solr.extract(fh, extractOnly=True)
                # generation du hash
                hash = hashlib.md5(fh.read()).hexdigest()
                if publication.acte_nature == "1":
                    traiter_deliberation(data, hash, infoEtablissement, publication, acte)
                elif publication.acte_nature == "5":
                    traiter_budget(data, hash, infoEtablissement, publication, acte)
                # insert dans apache solr
                solr.add(data['metadata'])

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
            with open(pj.path, 'rb') as fh:
                try:
                    solr = solr_connexion()
                    data = solr.extract(fh, extractOnly=True)
                    # generation du hash
                    hash = hashlib.md5(fh.read()).hexdigest()
                    traiter_pj(data, hash, infoEtablissement, publication, pj)

                    # insert dans apache solr
                    solr.add(data['metadata'])

                except pysolr.SolrError as e:
                    logging.exception("fichier ignore : %s" % pj)
    except Exception as e:
        logging.exception("probleme traitement PJ : on ignore")


def lien_symbolique_et_etat_solr(publication):
    if publication.acte_nature == "1":
        dossier = publication.siren + os.path.sep + "Deliberation"
    elif publication.acte_nature == "5":
        dossier = publication.siren + os.path.sep + "Budget"

    annee = str(publication.date_de_lacte.year)

    # copy de l'acte dans le dossier marque blanche
    for acte in publication.actes:
        symlink_file(acte.path,
                     current_app.config['DIR_MARQUE_BLANCHE'] + dossier + os.path.sep + annee + os.path.sep,
                     acte.name)

    # copy des pj dans le dossier marque blanche
    for pj in publication.pieces_jointe:
        symlink_file(pj.path,
                     current_app.config['DIR_MARQUE_BLANCHE'] + dossier + os.path.sep + annee + os.path.sep,
                     pj.name)

    solr = solr_connexion()
    result = solr.search(q='publication_id : ' + str(publication.id))
    # Mise à jour dans Solr
    for doc_res in result.docs:
        doc_res['est_publie'][0] = True
    solr.add(result.docs)


def traiter_pj(data, hash, infoEtablissement, publication, pj):
    dossier = "Budget"
    if publication.acte_nature == "1":
        dossier = publication.siren + os.path.sep + "Deliberation"
    elif publication.acte_nature == "5":
        dossier = publication.siren + os.path.sep + "Budget"

    if publication.date_budget:
        annee = publication.date_budget
    else:
        annee = str(publication.date_de_lacte.year)

    urlPDF = current_app.config['URL_MARQUE_BLANCHE'] + dossier + "/" + annee + "/" + pj.name

    parametrage = Parametrage.query.filter(Parametrage.siren == publication.siren).one()

    content = extract_content(data['contents'], "html5lib")

    # initialisation du document apache solr
    init_document(content, data, hash, infoEtablissement, parametrage, publication, urlPDF, "PJ")

    # dépot dans le serveur
    symlink_file(pj.path, current_app.config['DIR_MARQUE_BLANCHE'] + dossier + os.path.sep + annee + os.path.sep,
                 pj.name)
    return data['metadata']


def traiter_budget(data, hash, infoEtablissement, publication, acte):
    if publication.date_budget:
        annee = publication.date_budget
    else:
        annee = str(publication.date_de_lacte.year)

    dossier = publication.siren + os.path.sep + "Budget"
    urlPDF = current_app.config['URL_MARQUE_BLANCHE'] + dossier + "/" + annee + "/" + acte.name

    parametrage = Parametrage.query.filter(Parametrage.siren == publication.siren).one()

    content = extract_content(data['contents'], "xml")

    # initialisation du document apache solr
    init_document(content, data, hash, infoEtablissement, parametrage, publication, urlPDF, "99_BU")

    # dépot dans le serveur
    symlink_file(acte.path, current_app.config['DIR_MARQUE_BLANCHE'] + dossier + os.path.sep + annee + os.path.sep,
                 acte.name)
    return data['metadata']


def traiter_deliberation(data, hash, infoEtablissement, publication, acte):
    annee = str(publication.date_de_lacte.year)
    parametrage = Parametrage.query.filter(Parametrage.siren == publication.siren).one()
    dossier = publication.siren + os.path.sep + "Deliberation"
    urlPDF = current_app.config['URL_MARQUE_BLANCHE'] + dossier + "/" + annee + "/" + acte.name

    content = extract_content(data['contents'], "html5lib")

    # initialisation du document apache solr
    init_document(content, data, hash, infoEtablissement, parametrage, publication, urlPDF, "99_DE")

    # dépot dans le serveur
    symlink_file(acte.path, current_app.config['DIR_MARQUE_BLANCHE'] + dossier + os.path.sep + annee + os.path.sep,
                 acte.name)
    return data['metadata']


def init_document(content, data, hash, infoEtablissement, parametrage, publication, urlPDF, typology):
    data['metadata']['_text_'] = content
    data['metadata']["hash"] = hash
    data['metadata']["publication_id"] = publication.id
    data['metadata']["filepath"] = urlPDF
    data['metadata']["stream_content_type"] = data['metadata']["Content-Type"]
    # etat publication
    data['metadata']["est_publie"] = False
    data['metadata']["opendata_active"] = parametrage.open_data_active
    data['metadata']["date_budget"] = publication.date_budget
    # partie métadata (issu du fichier metadata.json de pastell)
    data['metadata']["date"] = publication.date_de_lacte.strftime("%Y-%m-%dT%H:%M:%SZ")
    data['metadata']["description"] = publication.objet
    data['metadata']["documentidentifier"] = publication.numero_de_lacte
    data['metadata']["documenttype"] = publication.acte_nature
    data['metadata']["classification"] = publication.classification_code + " " + publication.classification_nom,
    data['metadata']["classification_code"] = publication.classification_code,
    data['metadata']["classification_nom"] = publication.classification_nom,
    data['metadata']["typology"] = typology,
    # PARTIE RESULT API SIRENE
    data['metadata']["siren"] = publication.siren,
    data['metadata']["nic"] = infoEtablissement.nic,
    data['metadata'][
        "adresse1"] = infoEtablissement.numeroVoieEtablissement + " " + infoEtablissement.typeVoieEtablissement + " " + infoEtablissement.libelleVoieEtablissement,
    data['metadata']["adresse2"] = infoEtablissement.complementAdresseEtablissement,
    data['metadata']["ville"] = infoEtablissement.libelleCommuneEtablissement,
    data['metadata']["codepostal"] = infoEtablissement.codePostalEtablissement,
    data['metadata']["boitepostale"] = infoEtablissement.distributionSpecialeEtablissement,
    data['metadata']["cedex"] = infoEtablissement.codeCedexEtablissement,
    data['metadata']["categorie"] = infoEtablissement.categorieEntreprise,
    data['metadata']["categoriejuridique"] = infoEtablissement.categorieJuridiqueUniteLegale,
    data['metadata']["entity"] = infoEtablissement.denominationUniteLegale,
    data['metadata']["activite"] = infoEtablissement.activitePrincipaleUniteLegale,
    data['metadata']["nomenclatureactivite"] = infoEtablissement.nomenclatureActivitePrincipaleUniteLegale


def init_publication(metadataPastell):
    WORKDIR = get_or_create_workdir()
    # publication open data oui par défaut 0:oui / 1:non / 2:Ne sais pas
    pub_open_data = '0'
    date_budget = None
    if metadataPastell.acte_nature != "5":
        if metadataPastell.publication_open_data == '1' or metadataPastell.publication_open_data == '2':
            pub_open_data = metadataPastell.publication_open_data
    # SI acte BUDGET, alors on lit le fichier xml pour obtenir l'année
    else:
        xml_buget = WORKDIR + metadataPastell.liste_arrete[0]
        date_budget = __get_date_buget(xml_buget)

    db_sess = db.session
    newPublication = Publication(
        numero_de_lacte=metadataPastell.numero_de_lacte,
        objet=metadataPastell.objet,
        siren=metadataPastell.siren,
        publication_open_data=pub_open_data,
        date_de_lacte=metadataPastell.date_de_lacte,
        created_at=datetime.now(),
        modified_at=datetime.now(),
        date_budget=date_budget,
        classification_code=metadataPastell.classification_code,
        classification_nom=metadataPastell.classification_nom,
        acte_nature=metadataPastell.acte_nature,
        envoi_depot=metadataPastell.envoi_depot,
    )
    db_sess.add(newPublication)
    db_sess.commit()

    annee = str(newPublication.date_de_lacte.year)
    if newPublication.acte_nature == "1":
        dossier = newPublication.siren + os.path.sep + "Deliberation"
        urlPub = newPublication.siren + '/' + "Deliberation"
    elif newPublication.acte_nature == "5":
        dossier = newPublication.siren + os.path.sep + "Budget"
        urlPub = newPublication.siren + '/' + "Budget"

    contient_acte_tamponne = False
    for acte_tamponne in metadataPastell.liste_acte_tamponne:
        dossier_publication = current_app.config['DIR_PUBLICATION'] + dossier + os.path.sep + annee + os.path.sep
        newDoc = Acte(
            name=acte_tamponne,
            url=current_app.config['URL_PUBLICATION'] + urlPub + '/' + annee + '/' + urllib.parse.quote(
                acte_tamponne),
            path=dossier_publication + acte_tamponne,
            publication_id=newPublication.id
        )
        db_sess.add(newDoc)
        path = WORKDIR + acte_tamponne
        move_file(path, dossier_publication, acte_tamponne)
        contient_acte_tamponne = True

    # si on a pas d'acte tamponne on prend le fichier non tamponné
    if contient_acte_tamponne is False:
        for arrete in metadataPastell.liste_arrete:
            dossier_publication = current_app.config['DIR_PUBLICATION'] + dossier + os.path.sep + annee + os.path.sep
            newDoc = Acte(
                name=arrete,
                url=current_app.config['URL_PUBLICATION'] + urlPub + '/' + annee + '/' + urllib.parse.quote(
                    arrete),
                path=dossier_publication + arrete,
                publication_id=newPublication.id
            )
            db_sess.add(newDoc)
            path = WORKDIR + arrete
            move_file(path, dossier_publication, arrete)

    # Pour tous les fichiers pj présents dans le zip
    if metadataPastell.liste_autre_document_attache is not None:
        for pj in metadataPastell.liste_autre_document_attache:
            dossier_publication = current_app.config['DIR_PUBLICATION'] + dossier + os.path.sep + annee + os.path.sep
            newPj = PieceJointe(
                name=pj,
                url=current_app.config[
                        'URL_PUBLICATION'] + urlPub + '/' + annee + '/' + urllib.parse.quote(pj),
                path=dossier_publication + pj,
                publication_id=newPublication.id
            )
            db_sess.add(newPj)
            path = WORKDIR + pj
            move_file(path, dossier_publication, newPj.name)

    db_sess.commit()
    return newPublication


class MetadataPastell:
    def __init__(self, metajson):
        self.numero_de_lacte = metajson['numero_de_lacte']
        self.date_de_lacte = metajson['date_de_lacte']
        self.objet = metajson['objet']
        self.siren = metajson['siren']
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
        self.type_piece = metajson['type_piece']

        if 'publication_open_data' in metajson:
            self.publication_open_data = metajson['publication_open_data']
        else:
            self.publication_open_data = '0'

        self.acte_nature = metajson['acte_nature']
        self.classification = metajson['classification']

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


class InfoEtablissement:
    def __init__(self, resultApi):
        self.numeroVoieEtablissement = ''
        self.typeVoieEtablissement = ''
        self.libelleVoieEtablissement = ''
        self.complementAdresseEtablissement = ''
        self.distributionSpecialeEtablissement = ''
        self.codePostalEtablissement = ''
        self.libelleCommuneEtablissement = ''
        self.codeCedexEtablissement = ''
        self.categorieEntreprise = ''
        self.categorieJuridiqueUniteLegale = ''
        self.activitePrincipaleUniteLegale = ''
        self.nomenclatureActivitePrincipaleUniteLegale = ''
        self.denominationUniteLegale = ''
        self.nic = ''
        if resultApi['adresseEtablissement']['numeroVoieEtablissement'] != None:
            self.numeroVoieEtablissement = resultApi['adresseEtablissement']['numeroVoieEtablissement']
        if resultApi['adresseEtablissement']['typeVoieEtablissement'] != None:
            self.typeVoieEtablissement = resultApi['adresseEtablissement']['typeVoieEtablissement']
        if resultApi['adresseEtablissement']['libelleVoieEtablissement'] != None:
            self.libelleVoieEtablissement = resultApi['adresseEtablissement']['libelleVoieEtablissement']
        if resultApi['adresseEtablissement']['complementAdresseEtablissement'] != None:
            self.complementAdresseEtablissement = resultApi['adresseEtablissement']['complementAdresseEtablissement']
        if resultApi['adresseEtablissement']['distributionSpecialeEtablissement'] != None:
            self.distributionSpecialeEtablissement = resultApi['adresseEtablissement'][
                'distributionSpecialeEtablissement']
        if resultApi['adresseEtablissement']['codePostalEtablissement'] != None:
            self.codePostalEtablissement = resultApi['adresseEtablissement']['codePostalEtablissement']
        if resultApi['adresseEtablissement']['libelleCommuneEtablissement'] != None:
            self.libelleCommuneEtablissement = resultApi['adresseEtablissement']['libelleCommuneEtablissement']
        if resultApi['adresseEtablissement']['codeCedexEtablissement'] != None:
            self.codeCedexEtablissement = resultApi['adresseEtablissement']['codeCedexEtablissement']
        if resultApi['uniteLegale']['categorieEntreprise'] != None:
            self.categorieEntreprise = resultApi['uniteLegale']['categorieEntreprise']
        if resultApi['uniteLegale']['categorieJuridiqueUniteLegale'] != None:
            self.categorieJuridiqueUniteLegale = resultApi['uniteLegale']['categorieJuridiqueUniteLegale']
        if resultApi['uniteLegale']['activitePrincipaleUniteLegale'] != None:
            self.activitePrincipaleUniteLegale = resultApi['uniteLegale']['activitePrincipaleUniteLegale']
        if resultApi['uniteLegale']['nomenclatureActivitePrincipaleUniteLegale'] != None:
            self.nomenclatureActivitePrincipaleUniteLegale = resultApi['uniteLegale'][
                'nomenclatureActivitePrincipaleUniteLegale']
        if resultApi['uniteLegale']['denominationUniteLegale'] != None:
            self.denominationUniteLegale = resultApi['uniteLegale']['denominationUniteLegale']
        if resultApi['nic'] != None:
            self.nic = resultApi['nic']


def __get_date_buget(xml_file: str):
    namespaces = {'nms': 'http://www.minefi.gouv.fr/cp/demat/docbudgetaire'}

    tree = etree.parse(xml_file)
    annee = tree.findall('/nms:Budget/nms:BlocBudget/nms:Exer', namespaces)[0].attrib.get('V')
    return annee
