"""Fonctions pour monitorer la fin de copie d'un fichier"""

from pathlib import Path

import zipfile
import time
import os

from . import logger


def _current_milli_time():
    return round(time.time() * 1000)


def le_temps_de_surveillance_est_trop_long_fn(path: Path, temps_traitement_ms: int):
    old = _current_milli_time()

    def le_temps_de_surveillance_est_trop_long():
        nonlocal old
        nonlocal path

        current = _current_milli_time()
        elapsed = current - old

        logger.debug(f"Jusqu'à présent, la surveillance pour {path} a mis {elapsed} ms")
        if elapsed > temps_traitement_ms:
            logger.debug(f"C'est supérieur à la limite de {temps_traitement_ms} ms")
            return True
        else:
            return False

    return le_temps_de_surveillance_est_trop_long

def le_fichier_grossit_fn(path: Path, resolution_ms: int = 1000):
    old = _current_milli_time()
    old_taille = os.path.getsize(path)

    def le_fichier_a_grossit():
        nonlocal path
        nonlocal old
        nonlocal old_taille

        current = _current_milli_time()
        elapsed = current - old
        if elapsed < resolution_ms:
            # logger.debug(
            #     f"Pas assez de temps pour savoir si le {path} a grossit ({elapsed} ms). On considère que c'est le cas par défaut"
            # )
            return True

        old = current

        curr_taille = os.path.getsize(path)
        diff_taille = curr_taille - old_taille
        old_taille = curr_taille

        if diff_taille > 0:
            logger.debug(
                f"{path} a grossit de {diff_taille} octets depuis {elapsed} ms"
            )
            return True
        else:
            logger.debug(f"{path} n'a pas changé de taille depuis {elapsed} ms")
            return False

    return le_fichier_a_grossit


def le_fichier_est_un_zip_valide_fn(path: Path):
    def le_fichier_est_un_zip_valide():
        nonlocal path
        is_zipfile = zipfile.is_zipfile(path)
        if is_zipfile:
            logger.debug(f"{path} est un fichier zip valide")
            return True
        else:
            logger.debug(f"{path} est un fichier zip invalide")
            return False

    return le_fichier_est_un_zip_valide