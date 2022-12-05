from __future__ import annotations

import asyncio
from pathlib import Path
from typing import NoReturn

import typer
from harborapi import HarborAsyncClient
from pydantic import BaseModel
from pydantic import Field

from . import harbor
from .config import create_config
from .config import HarborCLIConfig
from .config import sample_config as get_sample_config

app = typer.Typer(help="Harbor CLI")


class State(BaseModel):
    """Class used to manage the state of the program.

    It is used as a global object that is accessible to all commands.
    """

    config: HarborCLIConfig = Field(default_factory=HarborCLIConfig)
    client: HarborAsyncClient = None  # type: ignore # will be patched by the callback
    verbose: bool = False
    loop: asyncio.AbstractEventLoop = Field(default_factory=asyncio.get_event_loop)

    class Config:
        keep_untouched = (asyncio.AbstractEventLoop,)
        arbitrary_types_allowed = True  # HarborAsyncClient
        validate_assignments = True
        extra = "allow"


state = State()


@app.callback()
def main(
    ctx: typer.Context,
    # Configuration options
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output."
    ),
    config: Path
    | None = typer.Option(None, "--config", "-c", help="Path to config file."),
    # Harbor options
    harbor_url: str | None = typer.Option(None, "--url", "-u", help="Harbor URL."),
    harbor_username: str
    | None = typer.Option(None, "--username", "-U", help="Harbor username."),
    harbor_secret: str | None = typer.Option(None),
    harbor_credentials: str
    | None = typer.Option(
        None, "--credentials", "-C", help="Harbor basic access credentials (base64)."
    ),
    harbor_credentials_file: Path
    | None = typer.Option(
        None, "--credentials-file", "-F", help="Harbor basic access credentials file."
    ),
):
    """
    Configuration options that affect all commands.
    """
    # These commands don't require state management
    # and can be run without a config file or client.
    if ctx.invoked_subcommand in ["sample-config", "init"]:
        return

    if verbose:
        state.verbose = True

    # Config file path
    if config:
        state.config = HarborCLIConfig.from_file(config)
    else:
        # Support creating config file if it doesn't exist
        # and no path has been specified
        state.config = HarborCLIConfig.from_file(create=True)

    state.client = harbor.get_client(state.config)


@app.command("init")
def init(
    path: Path | None = typer.Option(None, help="Path to create config file."),
    overwrite: bool = typer.Option(False, help="Overwrite existing config file."),
):
    """Initialize Harbor CLI."""
    typer.echo("Initializing Harbor CLI...")
    config_path = create_config(path, overwrite=overwrite)
    typer.echo(f"Created config file at {config_path}")
    # other initialization tasks here


@app.command("sample-config")
def sample_config():
    """Print a sample config file to stdout."""
    typer.echo(get_sample_config())


@app.command("vulnerabilities")
def vulnerabilities(
    project: str
    | None = typer.Option(
        None,
        "--project",
        "-p",
        help="Project name to list vulnerabilities for.",
    ),
    repo: str
    | None = typer.Option(
        None,
        "-r",
        "--repo",
        help="Repository name",
    ),
    tag: str
    | None = typer.Option(
        None,
        "-t",
        "--tag",
        help="Tag name",
    ),
    artifact: str
    | None = typer.Option(
        None,
        "-a",
        "--artifact",
        help="Complete name of artifact in the form of <project>/<repo>:<tag_or_digest>",
    ),
) -> None:
    def invalid_format_error() -> NoReturn:
        raise ValueError(
            "Artifact must be in the form of <project>/<repo>:<tag_or_digest>"
        )

    # TODO: move to own function
    if artifact is not None:
        parts = artifact.split("/")
        if len(parts) != 2:
            invalid_format_error()
        project, rest = parts
        parts = rest.split(":")
        if len(parts) != 2:
            invalid_format_error()
        repo, tag_or_digest = parts

    vulnerabilities = state.loop.run_until_complete(
        state.client.get_artifact_vulnerabilities(project, repo, tag_or_digest)
    )

    print(vulnerabilities)
