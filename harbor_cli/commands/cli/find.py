from __future__ import annotations

from enum import Enum
from typing import Callable
from typing import List
from typing import Optional

import typer
from fuzzywuzzy import fuzz

from ...app import app
from ...models import CommandSummary
from ...output.console import warning
from ...output.render import render_result
from ...utils.commands import get_app_commands


class MatchStrategy(Enum):
    """Match strategies."""

    RATIO = "ratio"
    PARTIAL_RATIO = "partial-ratio"
    TOKEN_SORT_RATIO = "token-sort-ratio"
    TOKEN_SET_RATIO = "token-set-ratio"


def get_match_func(strategy: MatchStrategy) -> Callable[[str, str], int]:
    """Get the match function for a strategy."""
    if strategy == MatchStrategy.RATIO:
        return fuzz.ratio
    elif strategy == MatchStrategy.PARTIAL_RATIO:
        return fuzz.partial_ratio
    elif strategy == MatchStrategy.TOKEN_SORT_RATIO:
        return fuzz.token_sort_ratio
    elif strategy == MatchStrategy.TOKEN_SET_RATIO:
        return fuzz.token_set_ratio
    else:
        raise ValueError(f"Unknown match strategy: {strategy}")  # pragma: no cover


def match_commands(
    commands: list[CommandSummary],
    query: str,
    min_score: int,
    names: bool,
    descriptions: bool,
    strategy: MatchStrategy,
) -> list[CommandSummary]:
    """Use fuzzy matching to find commands that match a query."""
    match_func = get_match_func(strategy)

    matches = []
    for command in commands:
        score = 0
        if names:
            name_score = match_func(query, command.name)
            if name_score > score:
                score = name_score
        if descriptions:
            desc_score = match_func(query, command.help)
            if desc_score > score:
                score = desc_score
        command.score = score
        if command.score >= min_score:
            matches.append(command)
    return sorted(matches, key=lambda x: x.score, reverse=True)


@app.command(no_args_is_help=True, name="find")
def find_command(
    ctx: typer.Context,
    query: List[str] = typer.Argument(
        ...,
        help="The search query.",
    ),
    limit: Optional[int] = typer.Option(
        None,
        help="Maximum number of results to show.",
        min=1,
    ),
    min_score: int = typer.Option(
        75,
        "--min-score",
        help="Minimum match ratio to show. Lower = more results.",
        min=0,
        max=100,
    ),
    names: bool = typer.Option(
        True,
        "--names/--no-names",
        help="Search in command names.",
    ),
    descriptions: bool = typer.Option(
        True,
        "--descriptions/--no-descriptions",
        help="Search in command descriptions.",
    ),
    strategy: MatchStrategy = typer.Option(
        MatchStrategy.PARTIAL_RATIO.value,
        "--strategy",
        help=(
            "The matching strategy to use. "
            "Strategies require different scoring thresholds. "
            "The default threshold is optimized for partial ratio."
        ),
    ),
) -> None:
    """Search for commands based on names and descriptions."""
    matches = _do_find(
        ctx=ctx,
        query=query,
        limit=limit,
        min_score=min_score,
        names=names,
        descriptions=descriptions,
        strategy=strategy,
    )
    render_result(matches, ctx)


def _do_find(
    ctx: typer.Context,
    query: List[str],
    limit: Optional[int],
    min_score: int,
    names: bool,
    descriptions: bool,
    strategy: MatchStrategy,
) -> list[CommandSummary]:
    # Join arguments to a single string
    q = " ".join(query)

    commands = get_app_commands(app)
    matches = match_commands(
        commands,
        q,
        min_score=min_score,
        names=names,
        descriptions=descriptions,
        strategy=strategy,
    )
    if limit is not None and len(matches) > limit:
        warning(f"{len(matches) - limit} results omitted.")
        matches = matches[:limit]
    return matches


@app.command(name="commands")
def list_commands(ctx: typer.Context) -> None:
    """List all commands."""
    commands = get_app_commands(app)
    render_result(commands, ctx)
