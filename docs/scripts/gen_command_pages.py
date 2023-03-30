"""Generate the code reference pages and navigation."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict
from typing import List

import jinja2
import yaml  # type: ignore
from sanitize_filename import sanitize

from harbor_cli.main import app
from harbor_cli.models import CommandSummary
from harbor_cli.utils.commands import get_app_commands

sys.path.append(Path(__file__).parent.as_posix())
sys.path.append(Path(__file__).parent.parent.parent.as_posix())

from common import COMMANDS_DIR  # noqa
from common import DATA_DIR  # noqa
from common import TEMPLATES_DIR  # noqa


# for path in sorted(SRC_PATH.rglob("*.py")):
#     module_path = path.relative_to(Path(".").resolve()).with_suffix("")
#     doc_path = path.relative_to(SRC_PATH).with_suffix(".md")
#     full_doc_path = Path(DOC_DIR / "reference", doc_path)

#     parts = tuple(module_path.parts)

#     if parts[-1] == "__init__":
#         parts = parts[:-1]
#         doc_path = doc_path.with_name("index.md")
#         full_doc_path = full_doc_path.with_name("index.md")
#     elif parts[-1] == "__main__":
#         continue

#     nav[parts] = doc_path.as_posix()

#     with mkdocs_gen_files.open(full_doc_path, "w") as fd:
#         ident = ".".join(parts)
#         fd.write(f"::: {ident}")

#     mkdocs_gen_files.set_edit_path(full_doc_path, Path("../") / path)


def gen_command_list(commands: list[CommandSummary]) -> None:
    command_names = [c.name for c in commands]
    with open(DATA_DIR / "commandlist.yaml", "w") as f:
        yaml.dump(command_names, f, sort_keys=False)


def gen_command_pages(commands: list[CommandSummary]) -> None:
    categories: Dict[str, List[CommandSummary]] = {}
    for command in commands:
        if command.hidden or command.deprecated:
            continue
        category = command.category or command.name
        if category not in categories:
            categories[category] = []
        categories[category].append(command)

    loader = jinja2.FileSystemLoader(searchpath=TEMPLATES_DIR)
    env = jinja2.Environment(loader=loader)

    # nav = mkdocs_gen_files.Nav()

    # Render each individual command page
    pages = {}  # type: dict[str, str] # {category: filename}
    for category_name, cmds in categories.items():
        template = env.get_template("category.md.j2")
        filename = sanitize(category_name.replace(" ", "_"))
        filepath = COMMANDS_DIR / f"{filename}.md"
        with open(filepath, "w") as f:
            f.write(template.render(category=category_name, commands=cmds))
        pages[category_name] = filename

    # Render the command list page
    template = env.get_template("command_list.md.j2")
    template.render(pages=pages)
    with open(COMMANDS_DIR / "index.md", "w") as f:
        f.write(template.render(pages=pages))

    # nav[]
    # with mkdocs_gen_files.open("reference/SUMMARY.txt", "w") as nav_file:
    #     nav_file.writelines(nav.build_literate_nav())


def main() -> None:
    commands = get_app_commands(app)
    gen_command_list(commands)
    gen_command_pages(commands)


if __name__ == "__main__":
    main()
