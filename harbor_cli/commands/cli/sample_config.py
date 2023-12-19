from __future__ import annotations

from ...app import app
from ...config import sample_config as get_sample_config
from ...output.console import print_toml


@app.command("sample-config")
def sample_config() -> None:
    """Print a sample config file to stdout."""
    print_toml(get_sample_config(), end="")  # no trailing newline
