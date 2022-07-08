# *****************************
# Environment specific settings
# *****************************
from celery.schedules import crontab
# DO NOT use "DEBUG = True" in production environments
DEBUG = True
# API SIREN V3
API_SIREN_KEY = 'xxxxxxxxxxxxxxxxxxx'
API_SIREN_SECRET = 'xxxxxxxxxxxxxxxxxxxxxxxxx'

# ***************************** AJOUT JULIEN *****************************
USE_BLOCKCHAIN = True
PRIVATE_KEY = '0x3a54e7c526de24a882e50452534f2a30dc7e491f253e2c784ca41382c59722d3'
PUBLIC_KEY = '0x82de905E53cB57Cfd7c1e9B7552a175756d96EFd'
NETWORK_NAME = 'Ropsten'
CONTRACT_ADDRESS = '0x3342b056Af4A655802074A4E09c0A10Ac086B4e9'
HTTP_PROVIDER = 'https://eth-ropsten.alchemyapi.io/v2/ej3ZztXfH3rAmUWlZS6pYLaavZdob2Ts'
BLOCKCHAIN_EXPLORER = 'https://ropsten.etherscan.io/tx/'
BLOCKCHAIN_ABI = '[{"inputs":[],"stateMutability":"nonpayable","type":"constructor"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"string","name":"_siren","type":"string"},{"indexed":false,"internalType":"string","name":"_url","type":"string"},{"indexed":false,"internalType":"uint256","name":"_timestamp","type":"uint256"}],"name":"NewPublication","type":"event"},{"inputs":[{"internalType":"string","name":"x","type":"string"}],"name":"existingInTab","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"getAllSirens","outputs":[{"internalType":"string[]","name":"","type":"string[]"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"string","name":"publisher_siren","type":"string"}],"name":"getSirenPublications","outputs":[{"components":[{"internalType":"string","name":"Publisher_siren","type":"string"},{"internalType":"string","name":"Doc_url","type":"string"},{"internalType":"uint256","name":"Doc_timestamp","type":"uint256"}],"internalType":"structmegalisV2.Publication[]","name":"","type":"tuple[]"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"string","name":"publisher_siren","type":"string"},{"internalType":"string","name":"doc_url","type":"string"}],"name":"publish","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"","type":"uint256"}],"name":"tab_publisher","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"}]'
# ***************************** AJOUT JULIEN *****************************

CELERY_BROKER_URL = 'redis://redis:6379/1'
result_backend = 'redis://redis:6379/0'

SECRET_KEY = "xxxxxxxxxxxxxxxxxxxxxxx"
#je sais pas quoi mettre car champ obligatoire et keycloak est en mode bearer only donc pas besoin de redirection
OIDC_REDIRECT_URI = 'http://localhost:5000'

# SQLAlchemy settings
#BASE DE DONNEE
SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://user:password@localhost:3306/data_extraction?charset=utf8'

SQLALCHEMY_TRACK_MODIFICATIONS = False    # Avoids a SQLAlchemy Warning

URL_PUBLICATION='https://data.megalis.bretagne.bzh/private/publications/'
DIR_PUBLICATION='/private/publications/'
DIR_ROOT_PUBLICATION='/public'

#URL marque blanche (outil gironde numérique)
URL_MARQUE_BLANCHE='https://data.megalis.bretagne.bzh/OpenData/'
DIR_MARQUE_BLANCHE='/public/OpenData/'

#info de connexion au serveur BDD ( pour creation des flux ged SFTP dans pastell)
DEPOT_HOSTNAME='x.x.x.x'
DEPOT_USERNAME="user"
DEPOT_PASSWORD="password"
#récupérer la valeur depuis l'ihm pastell dans un connecteur crée unitairement
DEPOT_FINGERPRINT='XXXXXXXXXXXXXXXXXXXXXXX'

#Pastell
API_PASTELL_URL='https://pastell.megalis.bretagne.bzh'
API_PASTELL_VERSION='/api/v2'
API_PASTELL_USER='user-pastell'
API_PASTELL_PASSWORD='password-pastell'

#apche solr
USER_SOLR='solr'
PASSWORD_SOLR='password'
URL_SOLR='https://xxxxxxxxx/solr/'
INDEX_DELIB_SOLR='sorl_core'

#watcher
WORKDIR = 'C:\\toWatch\\workdir\\'
DIRECTORY_TO_WATCH='D:\\toWatch\\in\\'
DIRECTORY_TO_WATCH_ARCHIVE='D:\\toWatch\\archive'
DIRECTORY_TO_PUBLICATION='D:\\toWatch\\publication'

DIRECTORY_RELAUNCH='D:\\toRelaunch\\'


#DATAGOUV - https://www.data.gouv.fr/fr/
API_DATAGOUV='https://www.data.gouv.fr/api/1'
API_KEY_DATAGOUV = 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
# orga megalis
ORG_MEGALIS_DATAGOUV = '534fff8ba3a7292c64a77ed3'
# https://www.data.gouv.fr/fr/datasets/donnees-essentielles-du-profil-acheteur-megalis-bretagne/
DATASET_MARCHE_DATAGOUV = '5f4f4f8910f4b55843deae51'
# https://www.data.gouv.fr/fr/datasets/deliberations-des-collectivites-adherentes-de-megalis-bretagne/
DATASET_DELIB_DATAGOUV = '60645c94e2bfd21cdc16c0be'
# https://www.data.gouv.fr/fr/datasets/budgets-des-collectivites-adherentes-de-megalis-bretagne/
DATASET_BUDGET_DATAGOUV = '60645b816cccca6dab67f532'

# Catalogue Udata
API_UDATA='https://mon.udata.fr/api/1'
API_KEY_UDATA='XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'


#Salle des marches Atexo
URL_JETON_SDM = 'https://xxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
URL_API_DECP='https://xxxxxxxxxxxxxx/app.php/api/v1/donnees-essentielles/contrat/format-pivot'

#CRON
CELERY_CRON = {
}
# CELERY_CRON = {
#     'publication_decp': {
#         'task': 'generation_marche',
#         'schedule': crontab(minute=0, hour=0)
#     }
# }
