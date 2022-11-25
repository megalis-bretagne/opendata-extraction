import logging
from logging import Logger
from typing import Union

def _level_name_to_int(level_name: str) -> Union[int, None]:
    level = logging.getLevelName(level_name)
    if not isinstance(level, int):
        return None
    return level

def setup_loggerlevel_from_levelname(level_name: str, *loggers: Logger):
    level = _level_name_to_int(level_name)
    if level is None:
        print(f"{level_name} n'est pas un niveau de log valide.")
        return

    print(f"Setting log level to {level_name} to {len(loggers)} logger(s)")
    for logger in loggers:
        logger.setLevel(level)
