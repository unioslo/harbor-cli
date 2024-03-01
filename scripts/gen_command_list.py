from __future__ import annotations

import sys
from pathlib import Path
from typing import Any
from typing import Dict
from typing import List

import yaml  # type: ignore

from harbor_cli.main import app
from harbor_cli.utils.commands import get_app_commands


sys.path.append(Path(__file__).parent.as_posix())
from common import DATA_DIR  # noqa


def main() -> None:
    commands = get_app_commands(app)
    command_names = [c.name for c in commands]

    categories: Dict[str, List[Dict[str, Any]]] = {}
    for command in commands:
        category = command.category or ""
        if category not in categories:
            categories[category] = []
        cmd_dict = command.model_dump()
        cmd_dict["usage"] = command.usage
        categories[category].append(cmd_dict)

    with open(DATA_DIR / "commands.yaml", "w") as f:
        yaml.dump(categories, f, sort_keys=False)

    with open(DATA_DIR / "commandlist.yaml", "w") as f:
        yaml.dump(command_names, f, sort_keys=False)


if __name__ == "__main__":
    main()
