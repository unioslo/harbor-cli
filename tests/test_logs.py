from __future__ import annotations

import logging
import os
from pathlib import Path

from harbor_cli.config import HarborCLIConfig
from harbor_cli.logs import disable_logging
from harbor_cli.logs import logger
from harbor_cli.logs import LogLevel
from harbor_cli.logs import replace_handler
from harbor_cli.logs import setup_logging
from harbor_cli.logs import update_logging


def test_log_level_as_int() -> None:
    assert LogLevel.NOTSET.as_int() == logging.NOTSET
    assert LogLevel.DEBUG.as_int() == logging.DEBUG
    assert LogLevel.INFO.as_int() == logging.INFO
    assert LogLevel.WARN.as_int() == logging.WARN
    assert LogLevel.WARNING.as_int() == logging.WARNING
    assert LogLevel.ERROR.as_int() == logging.ERROR
    assert LogLevel.FATAL.as_int() == logging.FATAL
    assert LogLevel.CRITICAL.as_int() == logging.CRITICAL


def test_setup_logging(config: HarborCLIConfig) -> None:
    disable_logging()
    assert not logger.handlers
    setup_logging(config.logging)
    assert logger.handlers
    handler = logger.handlers[0]
    assert handler.level == config.logging.level.as_int()
    # TODO: test filename


def test_update_logging(config: HarborCLIConfig, tmp_path: Path) -> None:
    logging_settings_pre = config.logging.model_copy()
    config.logging.level = LogLevel.WARNING
    config.logging.directory = tmp_path / "test_update_logging"
    config.logging.directory.mkdir(parents=True, exist_ok=True)

    # Update logging settings
    update_logging(config.logging)
    assert logger.handlers

    # Check that the handler was updated
    handler = logger.handlers[0]
    assert handler.level == config.logging.level.as_int()
    assert handler.baseFilename == os.path.abspath(config.logging.path)

    # Revert logging settings
    update_logging(logging_settings_pre)


def test_disable_logging(config: HarborCLIConfig) -> None:
    # Call disable_logging() twice to ensure it doesn't raise an exception
    disable_logging()
    disable_logging()
    assert not logger.handlers

    # Re-enable logging and then disable again
    setup_logging(config.logging)
    assert logger.handlers
    disable_logging()
    assert not logger.handlers
