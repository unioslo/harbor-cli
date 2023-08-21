from __future__ import annotations

import io
import os
from base64 import b64encode

import pytest
from harborapi import HarborAsyncClient

from harbor_cli.config import HarborCLIConfig
from harbor_cli.output.console import console
from harbor_cli.state import get_state
from harbor_cli.state import State


def test_state_run_nohandle(state: State) -> None:
    async def coro(exc_type: type[Exception]) -> int:
        raise exc_type("test")

    # Single error type
    with pytest.raises(ValueError):
        state.run(coro(ValueError), no_handle=ValueError)

    # Tuple of error types
    with pytest.raises(ValueError):
        state.run(coro(ValueError), no_handle=(ValueError, TypeError))
    with pytest.raises(TypeError):
        state.run(coro(TypeError), no_handle=(ValueError, TypeError))


@pytest.mark.timeout(1)  # timeout to avoid hanging on prompt
@pytest.mark.parametrize(
    "url",
    ["", "https://harbor.example.com/api/v2.0"],
)
@pytest.mark.parametrize(
    "username",
    ["username", ""],
)
@pytest.mark.parametrize(
    "secret",
    ["secret123", ""],
)
def test_state_init_client(
    monkeypatch: pytest.MonkeyPatch,
    # Fixture parameters
    url: str,
    username: str,
    secret: str,
) -> None:
    # Fresh state with default config
    state = State()

    state.config.harbor.url = url
    state.config.harbor.username = username
    state.config.harbor.secret = secret

    # Explicitly clear the other auth methods
    state.config.harbor.basicauth = ""
    state.config.harbor.credentials_file = None

    url_arg = url or "https://harbor.example.com/api/v2.0/default"
    username_arg = username or "username_arg"
    secret_arg = secret or "secret_arg"

    stdin = []
    if not url:
        stdin.append(url_arg)
    if not username or not secret:
        stdin.append(username_arg)
        stdin.append(secret_arg)
        # For some reason, patching sys.stdin fails for password prompts when
        # running in a terminal (zsh 5.8.1 (x86_64-apple-darwin21.0) && GNU bash, version 5.1.16(1)-release (aarch64-apple-darwin21.1.0))
        # on MacOS 12.6 (M1)
        # To work around this, we patch the underlying getpass._raw_input function
        monkeypatch.setattr(
            "getpass._raw_input", lambda prompt="", stream=None, input=None: secret_arg
        )
        assert not state.config.harbor.has_auth_method

    sep = os.linesep
    stdin_str = sep.join(stdin) + sep
    monkeypatch.setattr("sys.stdin", io.StringIO(stdin_str, newline=sep))

    state._init_client()

    # Test that we got prompted for the missing values and assigned to the client
    # NOTE: we don't store this info in the config in State when we prompt this way.
    # Should we do that?
    assert state.client.url == url_arg
    b = b64encode(f"{username_arg}:{secret_arg}".encode("utf-8")).decode("utf-8")
    assert state.client.basicauth.get_secret_value() == b


# Test properties that lazily initialize/assign values


def test_state_console() -> None:
    """Ensure that the console property uses the console object from harbor_cli.output.console"""
    state = State()
    assert state.console is console
    new_state = State()
    assert new_state.console is console


def test_state_client() -> None:
    """Ensure that the client property re-uses the same client object"""
    # de-init singleton for testing
    State._instance = None
    state = State()
    assert not state.is_client_loaded
    default_client = state.client  # the default client

    # Assign a client to the state to "load" it
    client = HarborAsyncClient(
        url="https://harbor.example.com/api/v2.0",
        basicauth="username:secret",
    )
    state.client = client
    assert state.is_client_loaded
    assert state.client is client
    assert state.client is not default_client

    # Modify client and then retrieve it
    state.client.basicauth = "username:secret"
    state.client.basicauth == "username:secret"
    assert state.client is client


def test_state_config() -> None:
    """Ensure that the client property re-uses the same client object"""
    # de-init singleton for testing
    State._instance = None
    state = State()
    # for testing purposes we
    assert not state.is_config_loaded
    default_config = state.config  # the default config

    # Assign a config to the state to "load" it
    config = HarborCLIConfig()
    state.config = config
    assert state.is_config_loaded
    assert state.config is config
    assert state.config is not default_config

    # Modify config and then retrieve it
    state.config.harbor.url = "https://harbor.example.com/api/v2.0"
    assert state.config is config
    assert (
        state.config.harbor.url
        == config.harbor.url
        == "https://harbor.example.com/api/v2.0"
    )

    # modify the config object directly (not through the state)
    config.harbor.url = "https://example.com"
    assert state.config.harbor.url == "https://example.com"


def test_get_state() -> None:
    state1 = get_state()
    state2 = get_state()
    state3 = State()
    assert state1 is state2 is state3
