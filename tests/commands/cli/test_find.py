from __future__ import annotations

import pytest
import typer

from ..._utils import Parameter
from harbor_cli.commands.cli.find import _do_find
from harbor_cli.commands.cli.find import MatchStrategy
from harbor_cli.models import CommandSummary

# Tests for the underlying _do_find() function


# TODO: more precise testing of this function
def test__do_find(mock_ctx: typer.Context) -> None:
    res = _do_find(
        mock_ctx,
        query=["ldap"],
        strategy=MatchStrategy.PARTIAL_RATIO,
        limit=None,
        min_score=75,
        names=True,
        descriptions=True,
    )
    assert len(res) > 0
    assert all(isinstance(r, CommandSummary) for r in res)


# Tests for the find command


def test_find_no_args(invoke) -> None:
    result = invoke(["find"])
    assert result.exit_code == 0
    # No argument is help
    assert result.output == invoke(["find", "--help"]).output


def test_find_query(invoke) -> None:
    result = invoke(["find", "ldap"])
    assert result.exit_code == 0
    assert result.output != ""


@pytest.mark.parametrize(
    "limit",
    [
        Parameter("--limit", "1"),
        Parameter("--limit", "0", ok=False),
        Parameter("--limit", "-1", ok=False),
        Parameter("--limit", "1000"),
    ],
)
@pytest.mark.parametrize("names", [Parameter("--names"), Parameter("--no-names")])
@pytest.mark.parametrize(
    "descriptions", [Parameter("--descriptions"), Parameter("--no-descriptions")]
)
def test_find_param(
    invoke,
    output_format_arg: list[str],
    limit: Parameter,
    names: Parameter,
    descriptions: Parameter,
) -> None:
    result = invoke(
        [
            *output_format_arg,
            "find",
            "ldap",
            *limit.as_arg,
            *descriptions.as_arg,
            *names.as_arg,
        ]
    )
    if any([not p.ok for p in [limit, names, descriptions]]):
        assert result.exit_code != 0, result.stderr
    else:
        assert result.exit_code == 0, result.output


def test_strategies_exist() -> None:
    assert len(list(MatchStrategy)) > 0


@pytest.mark.parametrize("strategy", list(MatchStrategy))
def test_find_strategies(invoke, strategy: MatchStrategy) -> None:
    # Test all valid strategies
    result = invoke(["find", "ldap", "--strategy", strategy.value])
    assert result.exit_code == 0


def test_find_invalid_strategy(invoke) -> None:
    # Invalid strategy
    invalid_strat = "random"
    with pytest.raises(ValueError):
        MatchStrategy(invalid_strat)  # assert this is invalid
    result = invoke(["find", "ldap", "--strategy", invalid_strat])
    assert result.exit_code != 0
