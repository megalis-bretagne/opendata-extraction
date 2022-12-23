import os
from pathlib import Path
import logging

import cProfile
import time
from typing import Optional
import uuid

_logger = logging.getLogger(__name__)

A_SECOND_NS = 1_000_000_000 
def profiling_to(root_dirname, only_above_s: Optional[int]=None):
    """Génère un dump cProfile pour la fonction

    Args:
        root_dirname (_type_): Nom du dossier contenant le dump
        only_above_s (_type_, optional): seuil au dessus duquel on export le profiling. Defaults to None.
    """

    def decorator(func):
        def inner(*args, **kwargs):

            p = Path(root_dirname)
            assert p.is_dir() or not p.exists(), f"{p} doit être un dossier"
            os.makedirs(p, exist_ok=True)
            p = p / f"{p.name}.{uuid.uuid4()}"

            with cProfile.Profile() as pr:
                start = time.perf_counter_ns()
                answer = func(*args, **kwargs)
                end = time.perf_counter_ns()
                elapsed = end - start
            
            if only_above_s is None or elapsed > (only_above_s * A_SECOND_NS):
                _logger.info(f"Dump profiling stats to {p}")
                pr.dump_stats(p)

            return answer
        return inner
    return decorator