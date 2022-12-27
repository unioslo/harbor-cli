from __future__ import annotations

import os
import subprocess

from common import DATA_PATH


if __name__ == "__main__":
    env = os.environ.copy()
    env["LINES"] = "40"
    env["COLUMNS"] = "80"

    # Get help text from the CLI
    help_text = subprocess.check_output(
        ["harbor", "--help"],
        env=env,
    ).decode("utf-8")
    with open(DATA_PATH / "help.txt", "w") as f:
        f.write(help_text)
