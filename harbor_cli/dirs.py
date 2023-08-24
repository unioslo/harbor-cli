from __future__ import annotations

from platformdirs import PlatformDirs

from .__about__ import APP_NAME
from .__about__ import AUTHOR
from .exceptions import DirectoryCreateError
from .logs import logger

_PLATFORM_DIR = PlatformDirs(APP_NAME, AUTHOR)
CONFIG_DIR = _PLATFORM_DIR.user_config_path
DATA_DIR = _PLATFORM_DIR.user_data_path
LOGS_DIR = _PLATFORM_DIR.user_log_path
SITE_CONFIG_DIR = _PLATFORM_DIR.site_config_path


def init_directories() -> None:
    for directory in [CONFIG_DIR, LOGS_DIR]:
        try:
            directory.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            # TODO: deduplicate these messages
            logger.error(
                f"Unable to create directory {directory}: {e}",
                exc_info=True,
            )
            raise DirectoryCreateError(f"Unable to create directory {directory}") from e
