from pathlib import Path
from flask import current_app
from flask.cli import AppGroup

from .watcher import Watcher

from . import logger

watcher_appgroup = AppGroup('watcher', help="Démarre le composant watcher open data")

@watcher_appgroup.command('observe-zipfiles', help="Surveille les fichiers zip dans l'option `DIRECTORY_TO_WATCH`")
def observe_dir():

    dir = current_app.config['DIRECTORY_TO_WATCH']
    dir = Path(dir)

    if not dir.is_dir():
        raise Exception(f"{dir} n'est pas un répertoire")
    
    logger.info(f"Observe le dossier {dir}")
    w = Watcher()
    w.run(dir)
    
