from contextlib import contextmanager
from typing import Union

import tempfile
import os
import errno

from flask import current_app
from . import logger

def _get_or_mkdir(dir):
    try:
        os.mkdir(dir)
    except OSError as exec:
        if exec.errno != errno.EEXIST:
            logger.warning("Impossible de créer {dir}")
            return None
    return dir

def _get_parent_temp_workdir() -> Union[str, None]:
    try:
        parent = None
        parent = current_app.config["TEMP_WORKDIR_PARENT"]
    except KeyError:
        logger.warning(
            '%s %s',
            "Le repertoire parent pour les dossiers temporaires n'est pas paramètré.",
            "Les dossiers temporaires se situeront dans /tmp/",
        )
        return parent
    
    parent = _get_or_mkdir(parent)
    return parent


@contextmanager
def temporary_workdir():
    """Generates a temporary working directoy ala tempfile.TemporaryDirectory"""
    try:
        parent = _get_parent_temp_workdir()
        with tempfile.TemporaryDirectory(prefix="temp_workdir", dir=parent) as dir:
            logger.debug(f"Création d'un dossier de travail temporaire: {dir}")
            yield dir
    finally:
        pass
