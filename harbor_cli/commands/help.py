from __future__ import annotations

from ..style import render_cli_value

ARTIFACT_HELP_STRING = (
    f"Name of the artifact in the format {render_cli_value('PROJECT/REPOSITORY{:tag,@sha256:digest}')}. "
    f"Example: {render_cli_value('library/nginx:latest')} or {render_cli_value('library/nginx@sha256:1234')}."
)
