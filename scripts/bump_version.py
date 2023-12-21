from __future__ import annotations

import subprocess
import sys
from enum import Enum
from typing import Any
from typing import Iterator
from typing import NamedTuple
from typing import Sequence

import typer
from rich.console import Console
from rich.panel import Panel

console = Console()
err_console = Console(stderr=True, style="red")


class BumpError(Exception):
    pass


class VersionType(Enum):
    major: str = "major"
    minor: str = "minor"
    patch: str = "patch"


class StatusType(Enum):
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


# TODO: some sort of check to ensure we don't tag twice (??)
# but we also need to allow for the case where we want to create
# a status tag for a version that already exists.

versions = [v.value for v in VersionType]
statuses = [s.value for s in StatusType]


class State(Enum):
    OLD_VERSION = 0  # before bumping version
    NEW_VERSION = 1  # after bumping version
    GIT_ADD = 2  # after git adding version file
    GIT_COMMIT = 3  # after git commit
    GIT_TAG = 4  # after git tag
    GIT_PUSH = 5  # after git push

    @classmethod
    def __missing__(cls, value: Any) -> State:
        return State.OLD_VERSION


class StateMachine:
    old_version: str | None = None
    new_version: str | None = None

    def __init__(self):
        self.state = State.OLD_VERSION

    def advance(self):
        self.state = State(self.state.value + 1)

    def revert(self) -> State:
        self.state = State(self.state.value - 1)
        return self.state

    def rewind(self) -> Iterator[State]:
        while self.state != State.OLD_VERSION:
            yield self.revert()


def set_version(version: str) -> None:
    # We don't verify that the version arg is valid, we just pass it
    # to hatch and let it handle it.
    # Worst case scenario, we get a non-zero exit code and the script exits
    p_version = subprocess.run(["hatch", "version", version])
    if p_version.returncode != 0:
        raise BumpError(f"Failed to set version: {p_version.stderr.decode()}")


def cleanup(state: StateMachine) -> None:
    for st in state.rewind():
        # from last to first
        # Best-effort cleanup
        try:
            if st == State.GIT_TAG:
                if not state.new_version:
                    raise ValueError("No new version to untag.")
                subprocess.run(["git", "tag", "-d", state.new_version])
            elif st == State.GIT_COMMIT:
                subprocess.run(["git", "revert", "HEAD"])
            elif st == State.GIT_ADD:
                subprocess.run(["git", "reset", "HEAD"])
            elif st == State.NEW_VERSION:
                if not state.old_version:
                    raise ValueError("No old version to revert to.")
                # Revert the version bump
                set_version(state.old_version)
        except Exception as e:
            print(f"Failed to revert state {state.state}: {e}", file=sys.stderr)


def main(
    version: str = typer.Argument(
        ...,
        help="Version bump to perform or new version to set.",
        metavar="[" + "|".join(versions) + "|x.y.z],[" + "|".join(statuses) + "]",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Perform a dry run, don't actually change anything.",
    ),
):
    """Bump the version of the project and create a new git tag.

    Examples:

    $ python bump_version.py minor

    $ python bump_version.py major,rc

    $ python bump_version.py 1.2.3 # generally don't use this
    """
    state = StateMachine()
    try:
        _main(version, dry_run, state)
    except Exception as e:
        err_console.print(e)
        cleanup(state)
        raise e


class CommandCheck(NamedTuple):
    program: str
    command: Sequence[str]
    message: str


REQUIRED_COMMANDS = [
    CommandCheck(
        program="Hatch",
        command=["hatch", "--version"],
        message="Hatch is not installed. Please install it with `pip install hatch`.",
    ),
    CommandCheck(
        program="Git",
        command=["git", "--version"],
        message="Git is not installed. Please install it.",
    ),
]


def _check_commands() -> None:
    """Checks that we have the necessary programs installed and available"""
    for command in REQUIRED_COMMANDS:
        try:
            subprocess.check_output(command.command)
        except FileNotFoundError:
            err_console.print(f"{command.message} :x:", style="bold red")
            raise typer.Exit(1)
        else:
            console.print(f"{command.program} :white_check_mark:")


def dryrun_subprocess_run(args, *aargs, **kwargs):
    """Wrapper around subprocess.run that prints the command and returns a dummy CompletedProcess"""
    print(f"Running: {args}")
    # We want to return the real version if we're checking the version
    if args == ["hatch", "version"]:
        return subprocess.run_orig(args=args, *aargs, **kwargs)
    return subprocess.CompletedProcess(args=args, returncode=0, stdout=b"", stderr=b"")


def _main(version: str, dry_run: bool, state: StateMachine) -> None:
    if dry_run:
        lines = [
            "[bold]Running in dry-run mode.[/bold]",
            "Commands will not be executed.",
            "",
            "[bold]NOTE:[/bold] The old package version will be shown in the previewed commands.",
        ]

        warning_console = Console(stderr=True, style="yellow")
        warning_console.print(
            Panel("\n".join(lines), title="Dry-run mode", expand=False)
        )
        # warning_console.print("[bold]Commands will not be executed.[/bold]")
        # warning_console.print(
        #     "[bold]NOTE: The old version package version will be shown in the Git commands in dry-run mode[/bold]"
        # )
        setattr(subprocess, "run_orig", subprocess.run)
        subprocess.run = dryrun_subprocess_run

    _check_commands()
    old_version = subprocess.check_output(["hatch", "version"])
    state.old_version = old_version.decode().strip()

    set_version(version)
    state.advance()
    assert state.state == State.NEW_VERSION

    # If this fails, something is very wrong.
    new_version = subprocess.check_output(["hatch", "version"]).decode().strip()
    err_console.print(f"New version: {new_version}")
    state.new_version = new_version

    # Create a new commit with the changed version file
    # TODO: add CHANGELOG.md too
    p_git_add = subprocess.run(["git", "add", "harbor_cli/__about__.py"])
    if p_git_add.returncode != 0:
        raise BumpError(f"Failed to add version file: {p_git_add.stderr.decode()}")
    state.advance()
    assert state.state == State.GIT_ADD

    p_git_commit = subprocess.run(
        ["git", "commit", "-m", f"Bump version to {new_version}"]
    )
    if p_git_commit.returncode != 0:
        raise BumpError(
            f"Failed to commit version bump: {p_git_commit.stderr.decode()}"
        )
    state.advance()
    assert state.state == State.GIT_COMMIT

    tag = f"harbor-cli-v{new_version}"
    p_git_tag = subprocess.run(["git", "tag", tag])
    if p_git_tag.returncode != 0:
        raise BumpError(f"Failed to tag version: {p_git_tag.stderr.decode()}")
    state.advance()
    assert state.state == State.GIT_TAG

    p_git_push = subprocess.run(["git", "push", "--tags", "origin", "main"])
    if p_git_push.returncode != 0:
        raise BumpError(f"Failed to push new version: {p_git_push.stderr.decode()}")
    state.advance()
    assert state.state == State.GIT_PUSH


if __name__ == "__main__":
    typer.run(main)
