"""Generate the code reference pages and navigation."""
from __future__ import annotations

import sys
from pathlib import Path

import mkdocs_gen_files

from docs.scripts.common import DOC_PATH
from docs.scripts.common import SRC_PATH

sys.path.append(Path(__file__).parent.parent.parent.as_posix())

nav = mkdocs_gen_files.Nav()

for path in sorted(SRC_PATH.rglob("*.py")):
    module_path = path.relative_to(Path(".").resolve()).with_suffix("")
    doc_path = path.relative_to(SRC_PATH).with_suffix(".md")
    full_doc_path = Path(DOC_PATH / "reference", doc_path)

    parts = tuple(module_path.parts)

    if parts[-1] == "__init__":
        parts = parts[:-1]
        doc_path = doc_path.with_name("index.md")
        full_doc_path = full_doc_path.with_name("index.md")
    elif parts[-1] == "__main__":
        continue

    nav[parts] = doc_path.as_posix()

    with mkdocs_gen_files.open(full_doc_path, "w") as fd:
        ident = ".".join(parts)
        fd.write(f"::: {ident}")

    mkdocs_gen_files.set_edit_path(full_doc_path, Path("../") / path)

with mkdocs_gen_files.open("reference/SUMMARY.txt", "w") as nav_file:
    nav_file.writelines(nav.build_literate_nav())
