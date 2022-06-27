# *****************************
# Environment specific settings
# *****************************
from celery.schedules import crontab
# DO NOT use "DEBUG = True" in production environments
DEBUG = True
# API SIREN V3
API_SIREN_KEY = 'xxxxxxxxxxxxxxxxxxx'
API_SIREN_SECRET = 'xxxxxxxxxxxxxxxxxxxxxxxxx'

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
