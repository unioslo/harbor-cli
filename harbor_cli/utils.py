from __future__ import annotations

from typing import Any
from typing import NoReturn


def replace_none(d: dict[str, Any], replacement: Any = "") -> dict[str, Any]:
    """Replaces None values in a dict with a given replacement value.
    Iterates recursively through nested dicts.
    Lists of depth 1 are also iterated through.

    Does not support list of dicts yet.
    Does not support containers other than dict and list.
    """
    if d is None:
        return replacement
    for key, value in d.items():
        if isinstance(value, dict):
            d[key] = replace_none(value)
        elif isinstance(value, list):
            d[key] = [item if item is not None else replacement for item in value]
        elif value is None:
            d[key] = replacement
    return d


def get_artifact_parts(s: str) -> tuple[str | None, str, str, str]:
    """Splits an artifact string into domain name (optional), project,
    repo, and tag_or_digest.

    Raises ValueError if the string is not in the correct format.
    """

    def _raise_value_error() -> NoReturn:
        raise ValueError(
            f"Artifact string {s} is not in the correct format. "
            "Expected format: [domain/]<project>/<repo>{@sha256:<digest>,:<tag>}"
        )

    parts = s.split("/")
    if len(parts) == 3:
        domain, project, rest = parts
    elif len(parts) == 2:
        project, rest = parts
        domain = None
    else:
        _raise_value_error()

    # TODO: make this more robust
    if "@" in rest:
        repo, tag_or_digest = rest.split("@")
    elif ":" in rest:
        parts = rest.split(":")
        if len(parts) != 2:
            _raise_value_error()
        repo, tag_or_digest = parts
    else:
        _raise_value_error()

    return domain, project, repo, tag_or_digest
