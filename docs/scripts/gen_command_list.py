from __future__ import annotations

import yaml  # type: ignore
from common import DATA_PATH

from harbor_cli.main import app
from harbor_cli.utils.commands import get_app_commands


if __name__ == "__main__":
    commands = get_app_commands(app)
    command_names = [c.name for c in commands]

    with open(DATA_PATH / "commands.txt", "w") as f:
        f.write("\n".join(command_names))

    with open(DATA_PATH / "commands.yaml", "w") as f:
        yaml.dump(command_names, f, sort_keys=False)
