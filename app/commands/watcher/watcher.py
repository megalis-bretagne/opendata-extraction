from pathlib import Path


from watchdog.events import FileSystemEventHandler, FileSystemEvent

from watchdog.observers.polling import PollingObserver

from . import logger
from .monitors import (
    le_fichier_grossit_fn,
    le_fichier_est_un_zip_valide_fn,
    le_temps_de_surveillance_est_trop_long_fn,
)

import time


class Watcher:
    def __init__(self) -> None:
        self.observer = PollingObserver()

    def run(self, dir: Path):

        event_handler = Handler()
        self.observer.schedule(event_handler, dir, recursive=True)
        logger.info(f"Démarre l'observation dans {dir}")
        self.observer.start()
        try:
            while True:
                time.sleep(5)
        except Exception as err:
            self.observer.stop()
            logger.error(f"Le watcher s'est arrêté")
            logger.exception(err)
        finally:
            self.observer.join()


class Handler(FileSystemEventHandler):
    @staticmethod
    def on_any_event(event: FileSystemEvent):
        if not event.is_directory and event.event_type == "created":
            path = Path(event.src_path)
            return Handler.on_create(path)

    @staticmethod
    def on_create(path: Path):

        from app.tasks.publication import creation_publication_task

        logger.info(f"Reçu l'evenement de création du fichier {path}")

        watchdog_ms = 600_000 # 10 minutes
        le_fichier_a_grossit = le_fichier_grossit_fn(path, resolution_ms=1_000)
        le_fichier_est_un_zip_valide = le_fichier_est_un_zip_valide_fn(path)
        le_temps_de_surveillance_est_trop_long = (
            le_temps_de_surveillance_est_trop_long_fn(path, watchdog_ms)
        )

        logger.info(
            f"Surveillons la fin de la copie pour {path}. Cela peut prendre du temps (max {watchdog_ms}ms)..."
        )

        while le_fichier_a_grossit() or not le_fichier_est_un_zip_valide():
            if le_temps_de_surveillance_est_trop_long():
                logger.warning(
                    f"On met trop de temps (> {watchdog_ms}ms) à surveiller si le fichier {path} a fini d'être copié. On le traite quand même."
                )
                break
            time.sleep(1)

        logger.info("Envoie de la tâche de traitement au worker.")
        creation_publication_task.delay(str(path))
        logger.info("Tâche envoyée")
