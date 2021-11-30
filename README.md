# Extraction open data megalis


L'application permet de gérer les publications opendata de Megalis Bretagne. 

En fonction du mode de lancement l'application:
* Expose une API REST (mode runserver)
* Déclenche des tâches périodique (mode beat)
* Exécute des tâches (mode worker)
* Scrute un répertoire (mode watcher)



***TODO** ajouter Lien vers la documentation : .readthedocs.


***TODO** mettre à jour le schéma*

## Les Technologies utilisées

* Python 3.9
* Flask
* Celery
* SQLAlchemy
* Apache Solr
* Mysql

## Mise en place d'un environnement de dev

We assume that you have `git` and `virtualenv` and `virtualenvwrapper` installed.

    # Clone the code repository into ~/dev/my_app
    mkdir -p ~/dev
    cd ~/dev
    git clone https://gxxxxxxxxxx.git my_app

    # Create the 'my_app' virtual environment
    mkvirtualenv -p PATH/TO/PYTHON my_app

    # Install required Python packages
    cd ~/dev/my_app
    workon my_app
    pip install -r requirements.txt

## Initialiser la BDD
    # Create DB tables and populate the roles and users tables
    python manage.py init_db

## Démarrer l'api REST 
    # Start the Flask development web server
    python manage.py runserver
Point your web browser to http://localhost:5000/doc

## Démarrer le watcher
    # Start the Flask development web server
    python manage.py watcher

## Démarrer un worker
    celery -A app.celeryapp.celery_worker.celery worker --pool=solo --loglevel=info -n worker1@%h

## Démarrer un orchestrateur (beat)
    celery -A app.celeryapp.celery_worker.celery beat --loglevel=info -s D:\\celerybeat-schedule.dat
