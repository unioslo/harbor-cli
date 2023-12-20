from __future__ import annotations

from pathlib import Path
from typing import Any
from typing import Callable

import pytest
from pytest import CaptureFixture
from pytest import LogCaptureFixture

from harbor_cli.config import LoggingSettings
from harbor_cli.logs import LogLevel
from harbor_cli.logs import update_logging
from harbor_cli.output.console import error
from harbor_cli.output.console import info
from harbor_cli.output.console import success
from harbor_cli.output.console import warning
from harbor_cli.state import State


def _configure_logging(
    settings: LoggingSettings, level: LogLevel, tmp_path: Path
) -> None:
    """Configure logging for the CLI."""
    settings.level = level
    settings.directory = tmp_path / "logs" / level.value.lower()
    settings.directory.mkdir(parents=True, exist_ok=True)
    update_logging(settings)


@pytest.fixture(scope="function", autouse=True)
def revert_logging(state: State) -> None:
    """Revert logging to the default settings after each test."""
    settings_pre = state.config.logging.model_copy()
    yield
    update_logging(settings_pre)


console_funcs = {
    # LogLevel.NOTSET: info,
    LogLevel.DEBUG: success,
    LogLevel.INFO: info,
    # LogLevel.WARN: warning,
    LogLevel.WARNING: warning,
    LogLevel.ERROR: error,
    # LogLevel.FATAL: error,
    # LogLevel.CRITICAL: error,
}


@pytest.mark.parametrize(
    "level,func",
    [
        # (LogLevel.NOTSET, info), # NYI
        (LogLevel.DEBUG, success),
        (LogLevel.INFO, info),
        # (LogLevel.WARN, warning),
        (LogLevel.WARNING, warning),
        (LogLevel.ERROR, error),
        # (LogLevel.FATAL, error), # NYI
        # (LogLevel.CRITICAL, critical), # NYI
    ],
)
def test_loglevels(
    state: State,
    capsys: CaptureFixture,
    caplog: LogCaptureFixture,
    tmp_path: Path,
    level: LogLevel,
    func: Callable[..., Any],
) -> None:
    """Tests that the logging performed by the console functions is correct,
    i.e. log levels are respected, the correct message is logged, and the
    file is in the expected location."""

    # Test logging with a level that matches the function
    _configure_logging(state.config.logging, level, tmp_path)
    test_str = f"testing {str(level.name).lower()}"
    func(test_str)
    captured = capsys.readouterr()
    assert test_str in captured.err
    assert len(caplog.records) == 1
    assert test_str in caplog.records[0].message
    assert test_str in state.config.logging.path.read_text()

    # Ensure that the log level is respected when level exceeds the function
    # i.e. calling info(...) when level is WARNING should not log to file, etc.
    for lvl in LogLevel:
        if lvl.as_int() <= level.as_int():
            continue
        _configure_logging(state.config.logging, lvl, tmp_path)
        test_str = f"Exceeded ({str(lvl.name).lower()} > {str(level.name).lower()})"
        func(test_str)
        captured = capsys.readouterr()
        assert test_str in captured.err
        assert test_str in caplog.text
        # Should not be logged to file
        assert test_str not in state.config.logging.path.read_text()
