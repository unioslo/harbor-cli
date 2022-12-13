from __future__ import annotations

from typing import NamedTuple

from ..exceptions import ArtifactNameFormatError


class ArtifactName(NamedTuple):
    domain: str | None
    project: str
    repository: str
    reference: str


def parse_artifact_name(s: str) -> ArtifactName:
    """Splits an artifact string into domain name (optional), project,
    repo, and reference (tag or digest).

    Raises ValueError if the string is not in the correct format.

    Parameters
    ----------
    s : str
        Artifact string in the form of [domain/]<project>/<repo>{@sha256:<digest>,:<tag>}

    Returns
    -------
    ArtifactName
        Named tuple of domain name (optional), project, repo, and reference (tag or digest).
    """
    parts = s.split("/")
    if len(parts) == 3:
        domain, project, rest = parts
    elif len(parts) == 2:
        project, rest = parts
        domain = None
    else:
        raise ArtifactNameFormatError(s)

    # TODO: make this more robust
    if "@" in rest:
        repo, tag_or_digest = rest.split("@")
    elif ":" in rest:
        parts = rest.split(":")
        if len(parts) != 2:
            raise ArtifactNameFormatError(s)
        repo, tag_or_digest = parts
    else:
        raise ArtifactNameFormatError(s)

    return ArtifactName(domain, project, repo, tag_or_digest)
