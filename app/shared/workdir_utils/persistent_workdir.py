import errno
import os
from flask import current_app

from . import logger

def get_or_create_persistent_workdir():
    WORKDIR = current_app.config['WORKDIR']
    # create workdir
    try:
        os.mkdir(WORKDIR)
    except OSError as exc:
        if exc.errno != errno.EEXIST:
            raise
        pass
    return WORKDIR

def clear_persistent_workdir():
    WORKDIR = get_or_create_persistent_workdir()
    filelist = [f for f in os.listdir(WORKDIR)]
    for f in filelist:
        try:
            workdir_f = os.path.join(WORKDIR, f)
            os.remove(workdir_f)
        except Exception as err:
            logger.warning(f"Echec lors de la suppression de {workdir_f}:")
            logger.exception(err)
    return WORKDIR