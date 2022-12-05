from __future__ import annotations

from pathlib import Path

from appdirs import AppDirs
from loguru import logger

from .__about__ import APP_NAME
from .__about__ import AUTHOR
from .exceptions import DirectoryCreateError

appdir = AppDirs(APP_NAME, AUTHOR)

CONFIG_DIR = Path(appdir.user_config_dir)
LOGS_DIR = Path(appdir.user_log_dir)


def init_directories() -> None:
    for directory in [CONFIG_DIR, LOGS_DIR]:
        try:
            directory.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            # TODO: deduplicate these messages
            logger.bind(exception=e).error(
                f"Unable to create directory {directory}: {e}"
            )
            raise DirectoryCreateError(f"Unable to create directory {directory}") from e
