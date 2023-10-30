from __future__ import annotations

import typer
from typer.models import OptionInfo

from harbor_cli.config import env_var
from harbor_cli.option import help_config_override
from harbor_cli.option import Option


def test_option() -> None:
    base_help = "Base help text."
    default = "default"
    info = Option(
        default,
        "--option",
        "-o",
        help=base_help,
        envvar=env_var("OPTION"),
        config_override="option",
    )

    # The help text should be updated with the config override info
    assert info.help == base_help + " " + help_config_override("option")
    assert info._help_original == base_help
    assert info.config_override == "option"
    # Test the rest of the attributes
    assert info.envvar == env_var("OPTION")
    assert info.param_decls == ("--option", "-o")
    assert info.default == default


def test_option_no_config_override() -> None:
    info = Option("default", "--option", "-o", help="Help text.")

    # The help text should be updated with the config override info
    assert info.help == "Help text."
    assert info._help_original == info.help
    # Test the rest of the attributes
    assert info.param_decls == ("--option", "-o")
    assert info.default == "default"


def test_option_no_help() -> None:
    info = Option("default", "--option", "-o")

    # The help text should be updated with the config override info
    assert info.help is None
    assert info._help_original is None
    # Test the rest of the attributes
    assert info.param_decls == ("--option", "-o")
    assert info.default == "default"


def test_option_subclass() -> None:
    args = (None, "--option", "-o")
    typer_option = typer.Option(*args)
    option = Option(*args)
    assert isinstance(option, OptionInfo)
    assert issubclass(option.__class__, OptionInfo)

    # Test that the subclass has the same attributes as the parent
    for attr in dir(typer_option):
        if attr.startswith("_"):
            continue

        # we explictly set these to false in the Option function
        if attr in ["show_default", "show_envvar"]:
            assert getattr(option, attr) is False
        else:
            # otherwise, the attributes should be the same
            assert getattr(typer_option, attr) == getattr(option, attr)
