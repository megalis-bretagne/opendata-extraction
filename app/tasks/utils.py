import csv
import hashlib
import logging
import pysolr, re, os, errno, shutil
import requests
from bs4 import BeautifulSoup
import paramiko
from functools import lru_cache
from api_insee import ApiInsee
from flask import current_app

@lru_cache(maxsize=25)
def api_insee_call(siren):
    if current_app.config['USE_API_INSEE']:
        api = ApiInsee(
            key=current_app.config['API_SIREN_KEY'],
            secret=current_app.config['API_SIREN_SECRET'],
        )
        data = api.siret(q={
            'siren': siren,
            'etablissementSiege': True
        }).get()
        if len(data['etablissements']) > 0:
            return InfoEtablissement(data['etablissements'][0])
        else:
            r = requests.get(current_app.config['URL_API_ENNTREPRISE'] + '/unites_legales/' + siren)
            if (r.status_code == 200):
                reponse = r.json()
                return InfoEtablissement(reponse['unite_legale'], False)
            else:
                return None
    else:
        r = requests.get(current_app.config['URL_API_ENNTREPRISE'] + '/unites_legales/' + siren)
        if (r.status_code == 200):
            reponse = r.json()
            return InfoEtablissement(reponse['unite_legale'], False)
        else:
            return None


def get_hash(filePath):
    BLOCK_SIZE = 65536  # The size of each read from the file
    file_hash = hashlib.sha256()
    with open(filePath, 'rb') as f:  # Open the file to read it's bytes
        fb = f.read(BLOCK_SIZE)  # Read from the file. Take in the amount declared above
        while len(fb) > 0:  # While there is still data being read from the file
            file_hash.update(fb)  # Update the hash
            fb = f.read(BLOCK_SIZE)  # Read the next block from the file
    return file_hash.hexdigest()


def solr_connexion():
    solr_address = current_app.config['URL_SOLR'] + "{}".format(current_app.config['INDEX_DELIB_SOLR'])
    solr = pysolr.Solr(solr_address, always_commit=True, timeout=120,
                       auth=(current_app.config['USER_SOLR'], current_app.config['PASSWORD_SOLR']))
    # # Do a health check.
    solr.ping()
    return solr


def solr_clear_all():
    solr_address = current_app.config['URL_SOLR'] + "{}".format(current_app.config['INDEX_DELIB_SOLR'])
    solr = pysolr.Solr(solr_address, always_commit=True, timeout=10,
                       auth=(current_app.config['USER_SOLR'], current_app.config['PASSWORD_SOLR']))
    # # Do a health check.
    solr.ping()
    solr.delete(q='*:*')
    return solr


def str_rep(in_str):
    in_str = in_str.replace("\n", '')
    out_str = re.sub('\s+', ' ', in_str)
    out_str = re.sub("[.]+", '', out_str)
    return out_str


def extract_content(solr_data, format):
    soup = BeautifulSoup(solr_data, format)
    out = [str_rep(x) for x in soup.stripped_strings]
    return " ".join(out)


def remove_file_sur_serveur(pathFile):
    ssh = paramiko.SSHClient()
    ssh.load_system_host_keys()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=current_app.config['DEPOT_HOSTNAME'], username=current_app.config['DEPOT_USERNAME'],
                password=current_app.config['DEPOT_PASSWORD'])
    # creation du repertoire si il n'existe pas
    ssh.exec_command("rm -f " + pathFile)
    ssh.close()


# def scp_sur_serveur(path,remote_path):
#    ssh = paramiko.SSHClient()
#    ssh.load_system_host_keys()
#    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
#    ssh.connect(hostname=current_app.config['DEPOT_HOSTNAME'],username=current_app.config['DEPOT_USERNAME'],password=current_app.config['DEPOT_PASSWORD'])
#    # creation du repertoire si il n'existe pas
#    ssh.exec_command("mkdir -p "+remote_path)
#    # SCPCLient takes a paramiko transport as an argument
#    scp = SCPClient(ssh.get_transport())
#    scp.put(path,remote_path=remote_path)
#    scp.close()
#
# def scp_sur_serveur_change_name(path, remote_path,nouveau_nom):
#    ssh = paramiko.SSHClient()
#    ssh.load_system_host_keys()
#    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
#    ssh.connect(hostname=current_app.config['DEPOT_HOSTNAME'], username=current_app.config['DEPOT_USERNAME'],
#                password=current_app.config['DEPOT_PASSWORD'])
#    # creation du repertoire si il n'existe pas
#    ssh.exec_command("mkdir -p " + remote_path)
#    # SCPCLient takes a paramiko transport as an argument
#    scp = SCPClient(ssh.get_transport())
#    scp.put(path, remote_path=remote_path+'/'+nouveau_nom)
#    scp.close()

def clear_wordir():
    WORKDIR = get_or_create_workdir()
    filelist = [f for f in os.listdir(WORKDIR)]
    for f in filelist:
        os.remove(os.path.join(WORKDIR, f))
    return WORKDIR


def get_or_create_workdir():
    WORKDIR = current_app.config['WORKDIR']
    # create workdir
    try:
        os.mkdir(WORKDIR)
    except OSError as exc:
        if exc.errno != errno.EEXIST:
            raise
        pass
    return WORKDIR


def query_result_to_csv(filename, result):
    outfile = open(get_or_create_workdir() + filename, "w")
    outcsv = csv.writer(outfile, lineterminator="\n")
    outcsv.writerow([row[0] for row in result.cursor.description])
    outcsv.writerows(result.cursor.fetchall())
    outfile.close()


def move_file(path, new_path, filename):
    # Create the directory
    try:
        os.makedirs(new_path, exist_ok=True)
        logging.info("Directory '%s' created successfully" % new_path)
    except OSError:
        logging.info("Directory '%s' can not be created" % new_path)
    shutil.move(path, new_path + filename)


def copy_file(path, new_path, filename):
    # Create the directory
    try:
        os.makedirs(new_path, exist_ok=True)
        logging.info("Directory '%s' created successfully" % new_path)
    except OSError:
        logging.info("Directory '%s' can not be created" % new_path)
    shutil.copyfile(path, new_path + filename)


def symlink_file(path, new_path, filename):
    # Create the directory
    try:
        os.makedirs(new_path, exist_ok=True)
        logging.info("Directory '%s' created successfully" % new_path)
    except OSError:
        logging.info("Directory '%s' can not be created" % new_path)
    try:
        os.symlink(path, new_path + filename)
    except FileExistsError:
        logging.exception("le lien existe deja")


nature_actes_dict = dict()
nature_actes_dict[1] = "Délibérations"
nature_actes_dict[2] = "Actes réglementaires"
nature_actes_dict[3] = "Actes individuels"
nature_actes_dict[4] = "Contrats,conventions et avenants"
nature_actes_dict[5] = "Documents budgétaires et financiers"
nature_actes_dict[6] = "Autres"

classification_actes_dict = dict()
classification_actes_dict[1] = "Commande Publique"
classification_actes_dict[1.1] = "Commande Publique/Marches publics"
classification_actes_dict[1.2] = "Commande Publique/Delegation de service public"
classification_actes_dict[1.3] = "Commande Publique/Conventions de Mandat"
classification_actes_dict[1.4] = "Commande Publique/Autres types de contrats"
classification_actes_dict[1.5] = "Commande Publique/Transactions /protocole d accord transactionnel"
classification_actes_dict[1.6] = "Commande Publique/Actes relatifs a la maitrise d oeuvre"
classification_actes_dict[1.7] = "Commande Publique/Actes speciaux et divers"

classification_actes_dict[2] = "Urbanisme"
classification_actes_dict[2.1] = "Urbanisme/Documents d urbanisme"
classification_actes_dict[2.2] = "Urbanisme/Actes relatifs au droit d occupation ou d utilisation des sols"
classification_actes_dict[2.3] = "Urbanisme/Droit de preemption urbain"

classification_actes_dict[3] = "Domaine et patrimoine"
classification_actes_dict[3.1] = "Domaine et patrimoine/Acquisitions"
classification_actes_dict[3.2] = "Domaine et patrimoine/Alienations"
classification_actes_dict[3.3] = "Domaine et patrimoine/Locations"
classification_actes_dict[3.4] = "Domaine et patrimoine/Limites territoriales"
classification_actes_dict[3.5] = "Domaine et patrimoine/Autres actes de gestion du domaine public"
classification_actes_dict[3.6] = "Domaine et patrimoine/Autres actes de gestion du domaine prive"

classification_actes_dict[4] = "Fonction publique"
classification_actes_dict[4.1] = "Fonction publique/Personnel titulaires et stagiaires de la F.P.T."
classification_actes_dict[4.2] = "Fonction publique/Personnel contractuel"
classification_actes_dict[4.3] = "Fonction publique/Fonction publique hospitaliere"
classification_actes_dict[4.4] = "Fonction publique/Autres categories de personnels"
classification_actes_dict[4.5] = "Fonction publique/Regime indemnitaire"

classification_actes_dict[5] = "Institutions et vie politique"
classification_actes_dict[5.1] = "Institutions et vie politique/Election executif"
classification_actes_dict[5.2] = "Institutions et vie politique/Fonctionnement des assemblees"
classification_actes_dict[5.3] = "Institutions et vie politique/Designation de representants"
classification_actes_dict[5.4] = "Institutions et vie politique/Delegation de fonctions"
classification_actes_dict[5.5] = "Institutions et vie politique/Delegation de signature"
classification_actes_dict[5.6] = "Institutions et vie politique/Exercice des mandats locaux"
classification_actes_dict[5.7] = "Institutions et vie politique/Intercommunalite"
classification_actes_dict[5.8] = "Institutions et vie politique/Decision d ester en justice"

classification_actes_dict[6] = "Libertes publiques et pourvoirs de police"
classification_actes_dict[6.1] = "Libertes publiques et pourvoirs de police/Police municipale"
classification_actes_dict[6.2] = "Libertes publiques et pourvoirs de police/Pouvoir du president du conseil general"
classification_actes_dict[6.3] = "Libertes publiques et pourvoirs de police/Pouvoir du president du conseil regional"
classification_actes_dict[6.4] = "Libertes publiques et pourvoirs de police/Autres actes reglementaires"
classification_actes_dict[
    6.5] = "Libertes publiques et pourvoirs de police/Actes pris au nom de l Etat et soumis au controle hierarchique"

classification_actes_dict[7] = "Finances locales"
classification_actes_dict[7.1] = "Finances locales/Decisions budgetaires"
classification_actes_dict[7.2] = "Finances locales/Fiscalite"
classification_actes_dict[7.3] = "Finances locales/Emprunts"
classification_actes_dict[7.4] = "Finances locales/Interventions economiques"
classification_actes_dict[7.5] = "Finances locales/Subventions"
classification_actes_dict[7.6] = "Finances locales/Contributions budgetaires"
classification_actes_dict[7.7] = "Finances locales/Avances"
classification_actes_dict[7.8] = "Finances locales/Fonds de concours"
classification_actes_dict[7.9] = "Finances locales/Prise de participation (SEM, etc...)"
classification_actes_dict[7.10] = "Finances locales/Divers"

classification_actes_dict[8] = "Domaines de competences par themes"
classification_actes_dict[8.1] = "Domaines de competences par themes/Enseignement"
classification_actes_dict[8.2] = "Domaines de competences par themes/Aide sociale"
classification_actes_dict[8.3] = "Domaines de competences par themes/Voirie"
classification_actes_dict[8.4] = "Domaines de competences par themes/Amenagement du territoire"
classification_actes_dict[8.5] = "Domaines de competences par themes/Politique de la ville-habitat-logement"
classification_actes_dict[8.6] = "Domaines de competences par themes/Emploi-formation professionnelle"
classification_actes_dict[8.7] = "Domaines de competences par themes/Transports"
classification_actes_dict[8.8] = "Domaines de competences par themes/Environnement"
classification_actes_dict[8.9] = "Domaines de competences par themes/Culture"

classification_actes_dict[9] = "Autres domaines de competences"
classification_actes_dict[9.1] = "Autres domaines de competences/Autres domaines de competences des communes"
classification_actes_dict[9.2] = "Autres domaines de competences/Autres domaines de competences des departements"
classification_actes_dict[9.3] = "Autres domaines de competences/Autres domaines de competences des regions"
classification_actes_dict[9.4] = "Autres domaines de competences/Voeux et motions"


class InfoEtablissement:
    def __init__(self, resultApi, API_INSEE):
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
        self.indiceRepetitionEtablissement = ''
        self.codeCommuneEtablissement = ''
        self.libelleCedexEtablissement = ''
        self.codePaysEtrangerEtablissement = ''
        self.libellePaysEtrangerEtablissement = ''
        self.etatAdministratifUniteLegale = ''
        self.statutDiffusionUniteLegale = ''
        self.dateCreationUniteLegale = ''
        self.sigleUniteLegale = ''
        self.caractereEmployeurUniteLegale = ''
        self.trancheEffectifsUniteLegale = ''
        self.anneeEffectifsUniteLegale = ''
        self.nicSiegeUniteLegale = ''
        self.anneeCategorieEntreprise = ''
        self.latitude = ''
        self.longitude = ''
        self.dateCreationEtablissement = ''
        self.trancheEffectifsEtablissement = ''
        self.anneeEffectifsEtablissement = ''
        self.activitePrincipaleRegistreMetiersEtablissement = ''

        if API_INSEE:
            if resultApi['adresseEtablissement']['numeroVoieEtablissement'] != None:
                self.numeroVoieEtablissement = resultApi['adresseEtablissement']['numeroVoieEtablissement']
            if resultApi['adresseEtablissement']['typeVoieEtablissement'] != None:
                self.typeVoieEtablissement = resultApi['adresseEtablissement']['typeVoieEtablissement']
            if resultApi['adresseEtablissement']['libelleVoieEtablissement'] != None:
                self.libelleVoieEtablissement = resultApi['adresseEtablissement']['libelleVoieEtablissement']
            if resultApi['adresseEtablissement']['complementAdresseEtablissement'] != None:
                self.complementAdresseEtablissement = resultApi['adresseEtablissement'][
                    'complementAdresseEtablissement']
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
        else:
            if resultApi['etablissement_siege']['latitude'] != None:
                self.latitude = resultApi['etablissement_siege']['latitude']
            if resultApi['etablissement_siege']['longitude'] != None:
                self.longitude = resultApi['etablissement_siege']['longitude']
            if resultApi['etablissement_siege']['nic'] != None:
                self.nic = resultApi['etablissement_siege']['nic']
            if resultApi['etablissement_siege']['siret'] != None:
                self.siret = resultApi['etablissement_siege']['siret']
            if resultApi['siren'] != None:
                self.siren = resultApi['siren']
            if resultApi['etablissement_siege']['date_creation'] != None:
                self.dateCreationEtablissement = resultApi['etablissement_siege']['date_creation']
            if resultApi['etablissement_siege']['tranche_effectifs'] != None:
                self.trancheEffectifsEtablissement = resultApi['etablissement_siege']['tranche_effectifs']
            if resultApi['etablissement_siege']['annee_effectifs'] != None:
                self.anneeEffectifsEtablissement = resultApi['etablissement_siege']['annee_effectifs']
            if resultApi['etablissement_siege']['activite_principale_registre_metiers'] != None:
                self.activitePrincipaleRegistreMetiersEtablissement = resultApi['etablissement_siege'][
                    'activite_principale_registre_metiers']
            if resultApi['etablissement_siege']['complement_adresse'] != None:
                self.complementAdresseEtablissement = resultApi['etablissement_siege']['complement_adresse']
            if resultApi['etablissement_siege']['numero_voie'] != None:
                self.numeroVoieEtablissement = resultApi['etablissement_siege']['numero_voie']
            if resultApi['etablissement_siege']['indice_repetition'] != None:
                self.indiceRepetitionEtablissement = resultApi['etablissement_siege']['indice_repetition']
            if resultApi['etablissement_siege']['type_voie'] != None:
                self.typeVoieEtablissement = resultApi['etablissement_siege']['type_voie']
            if resultApi['etablissement_siege']['libelle_voie'] != None:
                self.libelleVoieEtablissement = resultApi['etablissement_siege']['libelle_voie']
            if resultApi['etablissement_siege']['code_postal'] != None:
                self.codePostalEtablissement = resultApi['etablissement_siege']['code_postal']
            if resultApi['etablissement_siege']['libelle_commune'] != None:
                self.libelleCommuneEtablissement = resultApi['etablissement_siege']['libelle_commune']
            if resultApi['etablissement_siege']['code_commune'] != None:
                self.codeCommuneEtablissement = resultApi['etablissement_siege']['code_commune']
            if resultApi['etablissement_siege']['code_cedex'] != None:
                self.codeCedexEtablissement = resultApi['etablissement_siege']['code_cedex']
            if resultApi['etablissement_siege']['libelle_cedex'] != None:
                self.libelleCedexEtablissement = resultApi['etablissement_siege']['libelle_cedex']
            if resultApi['etablissement_siege']['code_pays_etranger'] != None:
                self.codePaysEtrangerEtablissement = resultApi['etablissement_siege']['code_pays_etranger']
            if resultApi['etablissement_siege']['libelle_pays_etranger'] != None:
                self.libellePaysEtrangerEtablissement = resultApi['etablissement_siege']['libelle_pays_etranger']
            if resultApi['etat_administratif'] != None:
                self.etatAdministratifUniteLegale = resultApi['etat_administratif']
            if resultApi['etablissement_siege']['statut_diffusion'] != None:
                self.statutDiffusionUniteLegale = resultApi['etablissement_siege']['statut_diffusion']
            if resultApi['etablissement_siege']['date_creation'] != None:
                self.dateCreationUniteLegale = resultApi['etablissement_siege']['date_creation']
            if resultApi['categorie_juridique'] != None:
                self.categorieJuridiqueUniteLegale = resultApi['categorie_juridique']
            if resultApi['denomination'] != None:
                self.denominationUniteLegale = resultApi['denomination']
            if resultApi['sigle'] != None:
                self.sigleUniteLegale = resultApi['sigle']
            if resultApi['etablissement_siege']['activite_principale'] != None:
                self.activitePrincipaleUniteLegale = resultApi['etablissement_siege']['activite_principale']
            if resultApi['etablissement_siege']['nomenclature_activite_principale'] != None:
                self.nomenclatureActivitePrincipaleUniteLegale = resultApi['etablissement_siege'][
                    'nomenclature_activite_principale']
            if resultApi['etablissement_siege']['caractere_employeur'] != None:
                self.caractereEmployeurUniteLegale = resultApi['etablissement_siege'][
                    'caractere_employeur']
            if resultApi['etablissement_siege']['tranche_effectifs'] != None:
                self.trancheEffectifsUniteLegale = resultApi['etablissement_siege']['tranche_effectifs']
            if resultApi['etablissement_siege']['annee_effectifs'] != None:
                self.anneeEffectifsUniteLegale = resultApi['etablissement_siege']['annee_effectifs']
            if resultApi['etablissement_siege']['nic'] != None:
                self.nicSiegeUniteLegale = resultApi['etablissement_siege']['nic']
            if resultApi['activite_principale'] != None:
                self.categorieEntreprise = resultApi['activite_principale']
            if resultApi['annee_categorie_entreprise'] != None:
                self.anneeCategorieEntreprise = resultApi['annee_categorie_entreprise']
