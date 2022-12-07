from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from ..app import app
from ..config import create_config
from ..output.console import console


@app.command("init")
def init(
    path: Optional[Path] = typer.Option(None, help="Path to create config file."),
    overwrite: bool = typer.Option(False, help="Overwrite existing config file."),
) -> None:
    """Initialize Harbor CLI."""
    console.print("Initializing Harbor CLI...")
    config_path = create_config(path, overwrite=overwrite)
    console.print(f"Created config file at {config_path}")
    # other initialization tasks here
