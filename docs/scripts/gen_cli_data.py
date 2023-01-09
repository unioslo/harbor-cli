"""Script that runs various CLI commands and collects the result for use
in the documentation.

The commands are run in a limited environment (no color, limited width) to
make the output more readable in the documentation.
"""
from __future__ import annotations

import os
import subprocess
from typing import NamedTuple

from common import DATA_PATH

# Set up environment variables for the CLI
env = os.environ.copy()
env["LINES"] = "40"
env["COLUMNS"] = "80"  # limit width so it looks nicer in MD code blocks
env["TERM"] = "dumb"  # disable color output (color codes mangle it)


class Command(NamedTuple):
    command: list[str]
    filename: str


# List of commands to run
COMMANDS = [
    Command(["harbor", "--help"], "help.txt"),
    Command(["harbor", "scanner", "list", "--help"], "help_scanner.txt"),
    Command(["harbor", "sample-config"], "sample_config.toml"),
]

if __name__ == "__main__":
    for cmd in COMMANDS:
        output = subprocess.check_output(cmd.command, env=env).decode("utf-8")
        with open(DATA_PATH / cmd.filename, "w") as f:
            f.write(output)
