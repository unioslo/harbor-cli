from __future__ import annotations

import logging

from harbor_cli.logs import LogLevel


def test_log_level_as_int() -> None:
    assert LogLevel.NOTSET.as_int() == logging.NOTSET
    assert LogLevel.DEBUG.as_int() == logging.DEBUG
    assert LogLevel.INFO.as_int() == logging.INFO
    assert LogLevel.WARN.as_int() == logging.WARN
    assert LogLevel.WARNING.as_int() == logging.WARNING
    assert LogLevel.ERROR.as_int() == logging.ERROR
    assert LogLevel.FATAL.as_int() == logging.FATAL
    assert LogLevel.CRITICAL.as_int() == logging.CRITICAL
