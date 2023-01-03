from __future__ import annotations

import subprocess
from enum import Enum
from typing import Optional

import typer


class VersionType(Enum):
    major: str = "major"
    minor: str = "minor"
    patch: str = "patch"


class ReleaseType(Enum):
    # Release
    release: str = "release"

    # Alpha
    a: str = "a"
    alpha: str = "alpha"

    # Beta
    b: str = "b"
    beta: str = "beta"

    # Release Candidate
    c: str = "c"
    rc: str = "rc"
    pre: str = "pre"
    preview: str = "preview"

    # Revision / Post
    r: str = "r"
    rev: str = "rev"
    post: str = "post"

    # Dev
    dev: str = "dev"


# Not all combinations of version type and release type are valid.
# but that is not checked here.

# TODO: some sort of check to ensure we don't tag twice (??)
# but we also need to allow for the case where we want to create
# a release tag for a version that already exists.


def main(
    version_type: VersionType = typer.Argument(
        ..., help="The type of version bump to perform"
    ),
    release_type: Optional[ReleaseType] = typer.Argument(
        None, help="The release type to use for the new version."
    ),
):
    """Bump the version of the project and create a new git tag.""" ""
    typer.echo(f"Version type: {version_type}")
    typer.echo(f"Release type: {release_type}")

    args = [version_type.value]
    if release_type:
        args.append(release_type.value)
    version_arg = ",".join(args)

    p_version = subprocess.run(["hatch", "version", version_arg])
    if p_version.returncode != 0:
        typer.echo(f"Failed to bump version: {p_version.stderr.decode()}")
        raise typer.Exit(1)

    # If this fails, something is very wrong.
    new_version = subprocess.check_output(["hatch", "version"]).decode().strip()
    typer.echo(f"New version: {new_version}")

    tag = f"harbor-cli-v{new_version}"
    p_git_tag = subprocess.run(["git", "tag", tag])
    if p_git_tag.returncode != 0:
        typer.echo(f"Failed to tag version: {p_git_tag.stderr.decode()}")
        raise typer.Exit(1)


if __name__ == "__main__":
    typer.run(main)
