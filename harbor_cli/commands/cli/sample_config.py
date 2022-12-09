from __future__ import annotations

from ...app import app
from ...config import sample_config as get_sample_config
from ...output.console import console


@app.command("sample-config")
def sample_config() -> None:
    """Print a sample config file to stdout."""
    console.print(get_sample_config())
