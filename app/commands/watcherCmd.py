# This file defines command line commands for manage.py
from pathlib import Path
from flask import current_app
from flask_script import Command
import logging

from app.commands.watcher.watcher import Watcher

class WatcherCommand(Command):
    def run(self):

        dir = current_app.config['DIRECTORY_TO_WATCH']
        dir = Path(dir)

        if not dir.is_dir():
            raise Exception(f"{dir} n'est pas un répertoire")
        
        logging.info(f"Observe le dossier {dir}")
        w = Watcher()
        w.run(dir)
